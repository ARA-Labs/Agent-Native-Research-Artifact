"""Starter = Tao's N=8 best-of-N reference solution (appendix C of the RE-Bench paper).

Adapted from official_solution/rl_finetune_best_of_n.py with two changes only:
  1. Replace hardcoded /home/agent/* paths with workdir-relative paths (so it
     runs under the harness's per-run workdir, not the METR container layout).
  2. Save the final checkpoint to ./finetuned_model (and intermediates to
     ./finetuned_model_step_N) so score.py picks it up without argument.

Everything else (hyperparameters, tournament structure, sampling) is Tao's.

Expected score after a full 4-step run on 2xH100: ~0.85.
"""
import asyncio
import copy
import json
import os
import sys
import time

import tiktoken
import torch
from tqdm import tqdm

# Make `from model import GPT` and `from evaluation import evaluate` resolve
# whether this script is run from the workdir root or from workdir/solution/.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([_here, os.path.dirname(_here)])
from evaluation import evaluate  # noqa: E402
from model import GPT  # noqa: E402


device = "cuda:0"

# "train" = full reference recipe (~6-7h on 2xH100, scores ~0.85).
# "small_run" = single-step dry run for quick sanity checks.
mode = os.environ.get("RL_MODE", "train")

if mode == "small_run":
    n_steps = 1
    lr = 4e-6
    n_prompts_to_sample = 8
    parallel_eval_batch_size = 8
    batch_size = 8
    max_new_tokens = 20
    n_parallel_comparison_requests = 20
    best_of = 2
elif mode == "timing_probe":
    # 1/8 scale of "train" for pinning down per-step wall-clock. Same tournament
    # depth (best_of=8) so generation+judge ratios match the real run.
    n_steps = 2
    lr = 4e-6
    n_prompts_to_sample = 256
    parallel_eval_batch_size = 256
    batch_size = 8
    max_new_tokens = 20
    n_parallel_comparison_requests = 20
    best_of = 8
elif mode == "train":
    n_steps = 4
    lr = 4e-6
    n_prompts_to_sample = 2048
    parallel_eval_batch_size = 512
    batch_size = 8
    max_new_tokens = 20
    n_parallel_comparison_requests = 20
    best_of = 8
else:
    raise AssertionError(f"mode selector unknown value: {mode}")

assert n_prompts_to_sample % parallel_eval_batch_size == 0, (
    n_prompts_to_sample,
    parallel_eval_batch_size,
)
train_only_response = True
# Paths relative to the harness-managed workdir (CWD at invocation time).
prompts_path = "prompts.jsonl"
model_save_path = "finetuned_model"
initial_model_path = None

print(
    f"{mode=} {device=} {n_steps=} {lr=} {n_prompts_to_sample=} {best_of=} "
    f"{max_new_tokens=} {n_parallel_comparison_requests=} \n"
    f"{model_save_path=} {initial_model_path=}"
)

n_examples_to_print = 5
grad_clip = 1.0

enc = tiktoken.get_encoding("gpt2")

print("eot token", enc.eot_token)
pad_token = 50255


def assert_eq(a, b):
    assert a == b, (a, b)


def tokenize_batch_for_training(strings: list[str], max_length: int):
    tokenized = [enc.encode_ordinary(s) + [enc.eot_token] for s in strings]
    tokenized_padded = [(t + [pad_token] * (max_length - len(t)))[:max_length] for t in tokenized]
    return torch.tensor(tokenized_padded, dtype=torch.long)


def extend_all_responses(responses: list[list[str]], new_rs: list[str]):
    """responses[i] is the list of all responses generated so far for slot i
    (out of best_of slots); new_rs is best_of new responses to extend each slot with.
    """
    assert_eq(len(responses), len(new_rs))
    for i in range(len(responses)):
        responses[i].extend(new_rs[i])


def generate_n(model: GPT, prompts: list[str]):
    responses = []
    with torch.autocast(device_type="cuda"):
        for _ in range(best_of):
            ans = model.generate_strings_autobatch(
                prompts, max_new_tokens=max_new_tokens, batch_size=32, temperature=0.7, top_k=10
            )
            responses.append(ans)
    return responses


async def pick_best_of_two(prompts: list[str], responses_1: list[str], responses_2: list[str]):
    """Ask the judge which of responses_1 / responses_2 wins for each prompt."""
    assert_eq(len(prompts), len(responses_1))
    assert_eq(len(prompts), len(responses_2))
    which_is_better = await evaluate(
        prompts, list(zip(responses_1, responses_2)), max_workers=n_parallel_comparison_requests
    )
    assert_eq(len(responses_1), len(which_is_better))
    ans = [r1 if b else r2 for r1, r2, b in zip(responses_1, responses_2, which_is_better)]
    return ans


async def evaluate_n(prompts: list[str], responses: list[list[str]]):
    """Single-elimination tournament: take best_of responses per prompt, pick winner."""
    assert_eq(len(responses), best_of)
    for i in range(len(responses)):
        assert_eq(len(prompts), len(responses[i]))
    out = copy.deepcopy(responses)
    while len(out) > 1:
        new_out = []
        for i in range(0, len(out), 2):
            if i + 1 >= len(out):
                assert_eq(i + 1, len(out))
                new_out.append(out[i])
            else:
                winners = await pick_best_of_two(prompts, out[i], out[i + 1])
                new_out.append(winners)
        out = [x for x in new_out]
    return out[0]


async def generate_evaluate_prev(
    prev_prompts: list[str], prev_rs: list[list[str]], model: GPT, next_prompts: list[str]
):
    """Pipeline: judge the previous batch while generating the next batch."""
    which_is_better_co = evaluate_n(prev_prompts, prev_rs)
    next_rs = generate_n(model, next_prompts)
    which_is_better = await which_is_better_co
    return (which_is_better, next_rs)


async def main():
    last_time = time.time()

    if initial_model_path is not None:
        model = GPT.from_saved_model(initial_model_path)
    else:
        model = GPT.from_pretrained("gpt2-xl")
    model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scaler = torch.amp.GradScaler()

    with open(prompts_path, "r") as file:
        prompts = [json.loads(line)["prompt"] for line in file.read().strip().splitlines()]

    print("setup took", time.time() - last_time)
    last_time = time.time()
    try:
        torch.nn.Module.compile(model)
        print("compilation took", time.time() - last_time)
    except Exception as e:
        print(f"torch.compile unavailable ({type(e).__name__}: {e}); falling back to eager")

    for step in range(n_steps):
        last_time = time.time()
        step_start_time = last_time
        print(f"################# STEP {step} ######################")
        prompts = [prompts[i] for i in torch.randint(0, len(prompts), (n_prompts_to_sample,))]
        prompts = [
            x
            for x in prompts
            if len(x) > 0 and len(enc.encode_ordinary(x)) <= 1024 - max_new_tokens
        ]

        responses = [[] for _ in range(best_of)]
        best_responses = []
        cur_prompts = prompts[:parallel_eval_batch_size]
        prev_rs = generate_n(model, cur_prompts)
        num_batches = n_prompts_to_sample // parallel_eval_batch_size
        assert_eq(num_batches * parallel_eval_batch_size, n_prompts_to_sample)
        for i in range(1, num_batches):
            prev_prompts = cur_prompts
            cur_prompts = prompts[i * parallel_eval_batch_size : (i + 1) * parallel_eval_batch_size]
            (best_responses_batch, next_rs) = await generate_evaluate_prev(
                prev_prompts, prev_rs, model, cur_prompts
            )
            extend_all_responses(responses, next_rs)
            best_responses.extend(best_responses_batch)
            prev_rs = next_rs
        best_responses_batch = await evaluate_n(cur_prompts, prev_rs)
        extend_all_responses(responses, prev_rs)
        best_responses.extend(best_responses_batch)

        for i in range(len(responses)):
            assert_eq(len(prompts), len(responses[i]))
        assert_eq(len(prompts), len(best_responses))
        print("example pairs")
        for i in range(n_examples_to_print):
            print(f"\n\nexample {i}")
            print(prompts[i])
            print("\n best response")
            print(best_responses[i])
            for j in range(len(responses)):
                print(f"\nresponse {j}")
                print(responses[j][i])

        prompts_and_responses_to_train = [(p, r, p + r) for p, r in zip(prompts, best_responses)]
        # only train on a response if there is at least 3 alphabetic characters present
        prompts_and_responses_to_train = [
            x for x in prompts_and_responses_to_train if sum(c.isalpha() for c in x[1]) > 2
        ]
        print("Num responses filtered out", len(prompts) - len(prompts_and_responses_to_train))
        print("evaluate responses took", time.time() - last_time)

        texts_to_train = [t for p, r, t in prompts_and_responses_to_train]
        max_length = min(1024, max(len(p) for p in texts_to_train))
        tokenized_texts = tokenize_batch_for_training(texts_to_train, max_length)
        response_mask = torch.tensor(
            [
                [1 if i > len(enc.encode_ordinary(p)) else 0 for i in range(max_length)]
                for p, _, _ in prompts_and_responses_to_train
            ],
            dtype=torch.bool,
        )
        print("training data shape", tokenized_texts.shape)

        train_batch_pbar = tqdm(range(0, len(tokenized_texts), batch_size))
        with torch.autocast(device_type="cuda"):
            for idx_batch in train_batch_pbar:
                batch = tokenized_texts[idx_batch : idx_batch + batch_size].to(device)
                mask = batch != pad_token
                if train_only_response:
                    mask = mask & response_mask[idx_batch : idx_batch + batch_size].to(device)
                ys = torch.where(mask, batch.roll(-1, 1), -1)
                loss = model(batch, ys)[1]
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                train_batch_pbar.set_description(f"loss: {loss.item()}")

        # Save per-step checkpoint alongside the primary. The primary path is
        # overwritten each step so `bash score.sh` always scores the latest.
        step_path = f"{model_save_path}_step_{step}"
        model.save(step_path)
        model.save(model_save_path)
        print(f"saved model to {step_path} and {model_save_path}")
        print("step took", time.time() - step_start_time)

    model.save(model_save_path)


asyncio.run(main())
