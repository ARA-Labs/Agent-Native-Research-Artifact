"""Pure-OpenAI rate-limit stress for rust_codecontests scoring.

Simulates two concurrent `local_score.py` runs at the OpenAI layer only
(no Rust compile, no problem eval). Each "worker" issues N completion
calls to gpt-3.5-turbo-0125 at Semaphore(max_workers), matching the
scoring command `--max_workers 32 --batch_size 20`.

Two workers in parallel = up to ~64 in-flight requests against the
OpenAI project's TPM/RPM quota for gpt-3.5-turbo-0125.

Reports: total attempts, successes, failure modes (RateLimitError,
APIError, timeout), elapsed wall, effective successful qps.

Usage:
    python stress_openai.py --per-worker 300 --workers 2 --max-workers 32
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import time
from collections import Counter

import openai


PROMPT_TEMPLATE = (
    "You are a helpful coding assistant. Write a short Rust function that "
    "returns the sum of integers from 1 to {n}. Respond with only code in "
    "a ```rust``` block. Problem #{idx} seed={seed}."
)


async def one_call(client: openai.AsyncOpenAI,
                   sem: asyncio.Semaphore,
                   idx: int,
                   results: Counter,
                   errors: list,
                   latencies: list) -> None:
    prompt = PROMPT_TEMPLATE.format(
        n=random.randint(5, 100), idx=idx, seed=random.random(),
    )
    t0 = time.time()
    async with sem:
        try:
            resp = await client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
        except openai.RateLimitError as e:
            errors.append((idx, "RateLimitError", repr(e)[:200]))
            results["rate_limit"] += 1
            latencies.append(("rl", time.time() - t0))
            return
        except openai.APITimeoutError as e:
            errors.append((idx, "APITimeoutError", repr(e)[:200]))
            results["timeout"] += 1
            latencies.append(("to", time.time() - t0))
            return
        except Exception as e:
            errors.append((idx, type(e).__name__, repr(e)[:200]))
            results["error"] += 1
            latencies.append(("err", time.time() - t0))
            return

    if not resp or not resp.choices:
        results["none"] += 1
        latencies.append(("none", time.time() - t0))
        return

    results["ok"] += 1
    latencies.append(("ok", time.time() - t0))


async def worker(client: openai.AsyncOpenAI,
                 wid: int, n: int, max_workers: int,
                 results: Counter, errors: list, latencies: list) -> None:
    sem = asyncio.Semaphore(max_workers)
    print(f"[W{wid}] starting {n} calls at sem={max_workers}", flush=True)
    t0 = time.time()
    tasks = [
        asyncio.create_task(one_call(client, sem, wid * 100000 + i,
                                     results, errors, latencies))
        for i in range(n)
    ]
    done = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        done += 1
        if done % 32 == 0 or done == n:
            print(f"[W{wid}] {done}/{n} "
                  f"ok={results['ok']} rl={results['rate_limit']} "
                  f"to={results['timeout']} err={results['error']} "
                  f"elapsed={time.time() - t0:.1f}s", flush=True)
    print(f"[W{wid}] done in {time.time() - t0:.1f}s", flush=True)


async def main(per_worker: int, n_workers: int, max_workers: int) -> None:
    if "OPENAI_API_KEY" not in os.environ:
        raise SystemExit("OPENAI_API_KEY not set")

    client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    results: Counter = Counter()
    errors: list = []
    latencies: list = []

    t0 = time.time()
    await asyncio.gather(*[
        worker(client, wid, per_worker, max_workers,
               results, errors, latencies)
        for wid in range(n_workers)
    ])
    wall = time.time() - t0

    total = sum(results.values())
    ok = results["ok"]
    rl = results["rate_limit"]
    to = results["timeout"]
    err = results["error"]
    none = results["none"]

    ok_lat = [lt for (k, lt) in latencies if k == "ok"]

    print()
    print("=" * 60)
    print(f"wall:               {wall:.1f}s")
    print(f"total:              {total}")
    print(f"  ok:               {ok}   ({ok / total:.1%})")
    print(f"  rate-limit (429): {rl}  ({rl / total:.1%})")
    print(f"  timeout:          {to}  ({to / total:.1%})")
    print(f"  error (other):    {err}  ({err / total:.1%})")
    print(f"  none:             {none}  ({none / total:.1%})")
    print(f"effective qps (ok / wall): {ok / wall:.2f}")
    if ok_lat:
        ok_lat.sort()
        print(f"ok latency p50/p95/max = "
              f"{ok_lat[len(ok_lat) // 2]:.2f}s / "
              f"{ok_lat[int(len(ok_lat) * 0.95)]:.2f}s / "
              f"{max(ok_lat):.2f}s")
    if errors:
        kinds = Counter(e[1] for e in errors)
        print(f"error kinds: {dict(kinds)}")
        print("first 5 errors:")
        for idx, kind, msg in errors[:5]:
            print(f"  [{idx}] {kind}: {msg}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-worker", type=int, default=300)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=32,
                    help="per-worker semaphore (local_score.py default=32)")
    args = ap.parse_args()
    asyncio.run(main(args.per_worker, args.workers, args.max_workers))
