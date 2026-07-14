"""Estimate unigram and bigram probability tables on OpenWebText.

Faithful port of ``measure_unigram_loss.py`` from the official solution at
``official_solutions/ai_rd_restricted_mlm/official_solution/``. Only
deviations:
  - ``device`` and ``data_dir`` / ``out_dir`` are CLI args (original hard-coded
    ``"cuda:7"`` and ``data/data/openwebtext``).
  - Outputs go to ``--out-dir`` (original dumped to CWD).
The arithmetic is unchanged.

Produces ``unigrams.pt``, ``bigrams_forward.pt``, ``bigrams_backward.pt``
in ``--out-dir``. These feed ``BiBigramMLM`` in the starter model.
"""
import argparse
import os

import numpy as np
import torch


def unigram_loss_efficient(sequence, vocab_size, out_dir, smoothing=1e-5):
    counts = torch.bincount(sequence, minlength=vocab_size).float()
    smoothed_counts = counts + smoothing
    probs = smoothed_counts / smoothed_counts.sum()
    torch.save(probs, os.path.join(out_dir, "unigrams.pt"))
    log_probs = torch.log(probs)
    nll = -log_probs[sequence].sum()
    return (nll / len(sequence)).item()


def bigram_loss(sequence, vocab_size, out_dir, smoothing=1e-5, backward=False):
    from_index = slice(0, -1) if not backward else slice(1, None)
    to_index = slice(1, None) if not backward else slice(0, -1)
    bigram_counts = torch.zeros(
        vocab_size, vocab_size, dtype=torch.float, device=sequence.device
    )
    bigram_indices = torch.stack([sequence[from_index], sequence[to_index]], dim=0)
    bigram_counts.index_put_(
        (bigram_indices[0], bigram_indices[1]),
        torch.ones(len(sequence) - 1, device=sequence.device),
        accumulate=True,
    )
    smoothed = bigram_counts + smoothing
    probs = smoothed / smoothed.sum(dim=1, keepdim=True)
    name = "bigrams_backward.pt" if backward else "bigrams_forward.pt"
    torch.save(probs, os.path.join(out_dir, name))
    log_probs = torch.log(probs)
    nll = -log_probs[sequence[from_index], sequence[to_index]].mean()
    return nll.item()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True,
                    help="directory containing train.bin")
    ap.add_argument("--out-dir", required=True,
                    help="directory to write unigrams.pt / bigrams_*.pt")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--vocab-size", type=int, default=50257)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    data = np.memmap(
        os.path.join(args.data_dir, "train.bin"), dtype=np.uint16, mode="r"
    )
    n_tokens = args.vocab_size * 200
    data_section = torch.from_numpy(data[:n_tokens].astype(np.int32)).to(args.device)

    print("bigram loss (forward):",
          bigram_loss(data_section, args.vocab_size, args.out_dir))
    print("bigram loss (backward):",
          bigram_loss(data_section, args.vocab_size, args.out_dir, backward=True))
    print("unigram loss:",
          unigram_loss_efficient(data_section, args.vocab_size, args.out_dir))


if __name__ == "__main__":
    main()
