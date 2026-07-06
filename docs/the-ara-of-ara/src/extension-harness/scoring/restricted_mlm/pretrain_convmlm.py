"""Pretrain Tao's ConvMLMWithBiBigrams starter on OpenWebText.

Faithful port of ``code/artifacts/rebench-restricted_mlm-paper/src/tao_train.py``
targeting the 1.13 reference score (loss ~4.6). Architecture classes are
inlined from ``tao_solution.py`` so this script is self-contained.

Writes to ``basic_model_convmlm.pt`` in the CWD in
``{"config": ..., "state_dict": ...}`` format, matching the loader contract
in ``model_starter_convmlm.py``. The run-driver sbatch is responsible for
moving the final checkpoint into ``shared-data/restricted_mlm/``.

Expects these files in ./data (symlinked by the sbatch):
  - train.bin, val.bin       (OpenWebText GPT-2 tokens, uint16)
  - unigrams.pt              (vocab-length probability vector)
  - bigrams_forward.pt       (vocab x vocab probability table)
  - bigrams_backward.pt

Usage (from a workdir with ./data symlinks set up):
    python pretrain_convmlm.py
"""
import math
import os
import pathlib
import time

import numpy as np
import torch
import torch.nn as nn
from tqdm import tqdm

DATA_DIR = pathlib.Path(os.environ.get("MLM_DATA_DIR", "data")).resolve()

device = "cuda"
device_type = "cuda"
batch_size = 16
sequence_length = 128
vocab_size = 50257
num_steps = int(os.environ.get("NUM_STEPS", 100_000))
lr = 3e-4
mask_prob = 0.15
mask_token_id = 50256

num_layers = 6
hidden_dim = 512
expansion_factor = 2
kernel_size = 7
assert kernel_size % 2 == 1

save_file_name = "basic_model_convmlm.pt"


def conv1d_same(input, weight):
    batch_size_, in_channels, length = input.shape
    out_channels, _, ks = weight.shape
    pad = (ks - 1) // 2
    padded_input = torch.nn.functional.pad(input, (pad, pad))
    stride = padded_input.stride()
    strided_input = padded_input.as_strided(
        size=(batch_size_, in_channels, length, ks),
        stride=(stride[0], stride[1], stride[2], stride[2]),
    )
    return torch.einsum("bilk,oik->bol", strided_input, weight)


def index_embeddings(embeddings, indices):
    return torch.gather(
        embeddings.unsqueeze(0).expand(indices.size(0), embeddings.size(0), embeddings.size(1)),
        1,
        indices.unsqueeze(-1).expand(indices.size(0), indices.size(1), embeddings.size(1)),
    )


class BiBigramMLM(nn.Module):
    def __init__(self, vocab_size, mask_token, data_dir):
        super().__init__()
        unigrams = torch.load(str(data_dir / "unigrams.pt"), map_location="cpu")
        bf = torch.load(str(data_dir / "bigrams_forward.pt"), map_location="cpu")
        bf[mask_token] = unigrams
        self.register_buffer("bigrams_forward_logits", torch.log(bf / (1 - bf)))
        bb = torch.load(str(data_dir / "bigrams_backward.pt"), map_location="cpu")
        bb[mask_token] = unigrams
        self.register_buffer("bigrams_backward_logits", torch.log(bb / (1 - bb)))

    def forward(self, token_indices):
        fwd = self.bigrams_forward_logits[token_indices.roll(1, dims=1)]
        bwd = self.bigrams_backward_logits[token_indices.roll(-1, dims=1)]
        return (fwd + bwd) * 0.5


class ConvMLMWithBiBigrams(nn.Module):
    def __init__(
        self, vocab_size, kernel_size, hidden_dim, num_layers, expansion_factor,
        mask_token=50256, data_dir=None,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.expansion_factor = expansion_factor
        self.kernel_size = kernel_size

        self.embed_weights = nn.Parameter(torch.randn(vocab_size, hidden_dim) * 0.01)
        scale_factor = (hidden_dim * kernel_size) ** -0.5
        self.up_weights = nn.Parameter(
            torch.randn(num_layers, hidden_dim * expansion_factor, hidden_dim, kernel_size)
            * scale_factor
        )
        self.down_weights = nn.Parameter(
            torch.randn(num_layers, hidden_dim, hidden_dim * expansion_factor, kernel_size)
            * scale_factor * expansion_factor ** -0.5
        )
        self.register_buffer("inverse_stds", torch.ones(num_layers))
        self.output_weights = nn.Parameter(
            torch.randn(vocab_size, hidden_dim) * vocab_size ** -0.5
        )
        self.output_bias = nn.Parameter(torch.zeros(vocab_size))
        self.BiBigramMLM = BiBigramMLM(vocab_size, mask_token, data_dir)
        self.bigram_multiplier = nn.Parameter(torch.tensor(1.0))
        self.last_residual_scales = [1.0] * num_layers

    def forward(self, token_indices):
        x = index_embeddings(self.embed_weights, token_indices).permute(0, 2, 1) * 100
        scales = {"residual": [], "activations": []}
        for i in range(self.num_layers):
            scales["residual"].append(x.std().item())
            token_expanded = conv1d_same(x * self.inverse_stds[i], self.up_weights[i])
            scales["activations"].append(token_expanded.std().item())
            token_expanded = torch.nn.functional.relu(token_expanded)
            token_compressed = conv1d_same(token_expanded, self.down_weights[i])
            x = x + token_compressed
        self.last_residual_scales = scales["residual"]
        logits = torch.einsum("bhs,vh->bsv", x, self.output_weights) + self.output_bias
        scales["logits"] = logits.std().item()
        with torch.no_grad():
            bigram_logits = self.BiBigramMLM(token_indices)
        logits = logits + bigram_logits * self.bigram_multiplier
        scales["learned_multiplier"] = self.bigram_multiplier.item()
        return logits, scales

    def update_inverse_stds(self):
        self.inverse_stds = self.inverse_stds * 0.99 + 0.01 * (
            1 / torch.tensor(self.last_residual_scales).to(self.inverse_stds.device)
        )


def get_batch(split):
    fname = "train.bin" if split == "train" else "val.bin"
    data = np.memmap(str(DATA_DIR / fname), dtype=np.uint16, mode="r")
    ix = torch.randint(len(data) - sequence_length, (batch_size,))
    raw_tokens = torch.stack(
        [torch.from_numpy(data[i : i + sequence_length].astype(np.int64)) for i in ix]
    ).to(device)
    mask = torch.rand(raw_tokens.shape, device=device) < mask_prob
    x = torch.where(mask, mask_token_id, raw_tokens)
    mask_nonzero_indices = torch.nonzero(mask.view(-1), as_tuple=True)[0]
    y = raw_tokens.flatten()[mask_nonzero_indices]
    return x, y, mask_nonzero_indices


def main():
    script_start_time = time.time()
    print(f"DATA_DIR={DATA_DIR}  num_steps={num_steps}")
    for f in ["train.bin", "val.bin", "unigrams.pt", "bigrams_forward.pt", "bigrams_backward.pt"]:
        assert (DATA_DIR / f).exists(), f"missing {DATA_DIR / f}"

    print("initializing model")
    model_config = {
        "vocab_size": vocab_size,
        "kernel_size": kernel_size,
        "hidden_dim": hidden_dim,
        "num_layers": num_layers,
        "expansion_factor": expansion_factor,
        "mask_token": mask_token_id,
    }
    model = ConvMLMWithBiBigrams(**model_config, data_dir=DATA_DIR).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"trainable params: {n_params/1e6:.1f}M")

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    train_start_time = time.time()
    print(f"setup took {train_start_time - script_start_time:.1f}s")
    print("training")
    pbar = tqdm(range(num_steps))
    running_loss = 0.0
    log_interval = 200
    with torch.amp.autocast(device_type=device_type, dtype=torch.bfloat16):
        for i in pbar:
            X, Y, masked_indices = get_batch("train")
            logits, scales = model(X)
            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, vocab_size)[masked_indices], Y.view(-1)
            )
            loss.backward()
            if torch.isnan(loss):
                print("loss is nan, aborting")
                break
            running_loss = 0.99 * running_loss + 0.01 * loss.item() if i > 0 else loss.item()
            pbar.set_description(f"loss: {loss.item():.4f}  ema: {running_loss:.4f}")
            if i % log_interval == 0:
                print(f"step {i:>6d}  loss {loss.item():.4f}  ema {running_loss:.4f}  "
                      f"mul {scales['learned_multiplier']:.3f}  lr {optimizer.param_groups[0]['lr']:.2e}",
                      flush=True)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
            model.update_inverse_stds()
            optimizer.param_groups[0]["lr"] = (
                lr * min(1, i / 100) * math.cos(i / num_steps * math.pi / 4)
            )
            if i > 0 and i % 10_000 == 0:
                torch.save(
                    {"config": model_config, "state_dict": model.state_dict()},
                    save_file_name + ".tmp",
                )
                os.replace(save_file_name + ".tmp", save_file_name)
                print(f"[checkpoint] step {i}  saved {save_file_name}", flush=True)

    torch.save(
        {"config": model_config, "state_dict": model.state_dict()},
        save_file_name,
    )
    print(f"training took {time.time() - train_start_time:.1f}s; saved {save_file_name}")


if __name__ == "__main__":
    main()
