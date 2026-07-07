"""Pure-Replicate rate-limit stress for nanogpt_chat_rl scoring.

Simulates two concurrent `score.py` runs at the Replicate layer only (no
GPU, no model generation). Each "worker" issues N judge calls to
meta/meta-llama-3-8b-instruct at Semaphore(20), matching evaluation.py.
Two workers in parallel = up to ~40 in-flight requests, at the edge of
the documented 50-burst limit for sub-$20 Replicate credit.

Reports: total attempts, successes, failure modes (ReplicateError, HTTP
429, timeouts, None responses), elapsed wall, effective successful qps.

Usage:
    python stress_replicate.py --per-worker 256 --workers 2 --max-workers 20
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import time
from collections import Counter

# Use the real evaluator's _generate (with retry-on-429) so the stress test
# exercises the same code path that scoring will hit in production.
from evaluation import _generate

PROMPT_TEMPLATE = (
    "Rank these two model outputs by quality. "
    "Prompt: {p}\nModel 1: short answer A.\nModel 2: short answer B.\n"
    "Return JSON: [{{\"model\":\"model_1\",\"rank\":1}},{{\"model\":\"model_2\",\"rank\":2}}]."
)


async def one_call(sem: asyncio.Semaphore, idx: int,
                   results: Counter, errors: list, latencies: list) -> None:
    prompt = PROMPT_TEMPLATE.format(p=f"test prompt {idx} {random.random():.4f}")
    t0 = time.time()
    async with sem:
        try:
            response = await _generate(
                prompt,
                system_prompt="You rank model outputs.",
                temperature=0.0,
                max_tokens=100,
            )
        except Exception as e:
            errors.append((idx, type(e).__name__, repr(e)[:200]))
            results["error"] += 1
            latencies.append(("err", time.time() - t0))
            return
    if response is None:
        # _generate returns None after exhausting retries (or on a non-429
        # error it has already printed). Count as failure for the test.
        results["none"] += 1
        latencies.append(("none", time.time() - t0))
        return
    results["ok"] += 1
    latencies.append(("ok", time.time() - t0))


async def worker(wid: int, n: int, max_workers: int,
                 results: Counter, errors: list, latencies: list) -> None:
    sem = asyncio.Semaphore(max_workers)
    print(f"[W{wid}] starting {n} calls at sem={max_workers}", flush=True)
    t0 = time.time()
    tasks = [
        asyncio.create_task(one_call(sem, wid * 100000 + i,
                                     results, errors, latencies))
        for i in range(n)
    ]
    done = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        done += 1
        if done % 32 == 0 or done == n:
            print(f"[W{wid}] {done}/{n} ok={results['ok']} err={results['error']} none={results['none']} "
                  f"elapsed={time.time()-t0:.1f}s",
                  flush=True)
    print(f"[W{wid}] done in {time.time()-t0:.1f}s", flush=True)


async def main(per_worker: int, n_workers: int, max_workers: int) -> None:
    if "REPLICATE_API_TOKEN" not in os.environ:
        raise SystemExit("REPLICATE_API_TOKEN not set")

    results = Counter()
    errors: list = []
    latencies: list = []

    t0 = time.time()
    await asyncio.gather(*[
        worker(wid, per_worker, max_workers, results, errors, latencies)
        for wid in range(n_workers)
    ])
    wall = time.time() - t0

    total = sum(results.values())
    ok = results["ok"]
    err = results["error"]
    none = results["none"]

    ok_lat = [lt for (k, lt) in latencies if k == "ok"]
    err_lat = [lt for (k, lt) in latencies if k == "err"]

    print()
    print("=" * 60)
    print(f"wall:          {wall:.1f}s")
    print(f"total:         {total}")
    print(f"  ok:          {ok}  ({ok / total:.1%})")
    print(f"  err:         {err}  ({err / total:.1%})")
    print(f"  none:        {none}  ({none / total:.1%})")
    print(f"effective qps (ok / wall): {ok / wall:.2f}")
    if ok_lat:
        ok_lat.sort()
        print(f"ok latency   p50/p95/max = "
              f"{ok_lat[len(ok_lat)//2]:.2f}s / "
              f"{ok_lat[int(len(ok_lat)*0.95)]:.2f}s / "
              f"{max(ok_lat):.2f}s")
    if err_lat:
        err_lat.sort()
        print(f"err latency  p50/p95/max = "
              f"{err_lat[len(err_lat)//2]:.2f}s / "
              f"{err_lat[int(len(err_lat)*0.95)]:.2f}s / "
              f"{max(err_lat):.2f}s")
    if errors:
        kinds = Counter(e[1] for e in errors)
        print(f"error kinds: {dict(kinds)}")
        print("first 5 errors:")
        for idx, kind, msg in errors[:5]:
            print(f"  [{idx}] {kind}: {msg}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-worker", type=int, default=256)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=20,
                    help="per-worker semaphore size (evaluation.py default=20)")
    args = ap.parse_args()
    asyncio.run(main(args.per_worker, args.workers, args.max_workers))
