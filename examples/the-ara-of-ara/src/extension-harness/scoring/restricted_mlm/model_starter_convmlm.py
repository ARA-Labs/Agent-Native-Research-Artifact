"""ConvMLM+BiBigrams starter (Tao's reference arch, not shipped to agent yet).

Kept parallel to ``model_starter.py`` (MLP starter) while we test whether
``pretrain_convmlm.py`` actually reaches the 1.13 reference score. If it
does, this file becomes ``model_starter.py`` and we pivot the starter back.

``get_trained_model()`` loads ``basic_model_convmlm.pt`` co-located with
this file. The checkpoint is produced by ``pretrain_convmlm.py``.

Matches the inference-forward restrictions: no conv1d layer, no gelu/softmax/
layer_norm. The one ``torch.log`` call is on bigram probability tables which
are materialized as fixed buffers at init time; the forward pass itself does
not call torch.log (it uses the precomputed logit tables).
"""
import os
import pathlib

import torch
import torch.nn as nn


def conv1d_same(input, weight):
    b, c, l = input.shape
    _, _, ks = weight.shape
    pad = (ks - 1) // 2
    padded = torch.nn.functional.pad(input, (pad, pad))
    stride = padded.stride()
    strided = padded.as_strided(
        size=(b, c, l, ks),
        stride=(stride[0], stride[1], stride[2], stride[2]),
    )
    return torch.einsum("bilk,oik->bol", strided, weight)


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


class Model(nn.Module):
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

    def forward(self, token_indices: torch.Tensor) -> torch.Tensor:
        x = index_embeddings(self.embed_weights, token_indices).permute(0, 2, 1) * 100
        for i in range(self.num_layers):
            token_expanded = conv1d_same(x * self.inverse_stds[i], self.up_weights[i])
            token_expanded = torch.nn.functional.relu(token_expanded)
            token_compressed = conv1d_same(token_expanded, self.down_weights[i])
            x = x + token_compressed
        logits = torch.einsum("bhs,vh->bsv", x, self.output_weights) + self.output_bias
        bigram_logits = self.BiBigramMLM(token_indices)
        logits = logits + bigram_logits * self.bigram_multiplier
        return logits


def get_trained_model():
    here = pathlib.Path(os.path.abspath(__file__)).parent
    ckpt_path = here / "basic_model.pt"
    if not ckpt_path.exists():
        ckpt_path = here / "basic_model_convmlm.pt"
    data_dir = pathlib.Path(os.environ.get("MLM_DATA_DIR", here.parent / "data"))
    saved = torch.load(str(ckpt_path), map_location="cpu")
    model = Model(**saved["config"], data_dir=data_dir)
    model.load_state_dict(saved["state_dict"])
    return model
