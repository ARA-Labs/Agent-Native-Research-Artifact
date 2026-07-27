# Problem

**Central question** (established Turn 1, N01): is learning better networks as easy as
stacking more layers? The paper motivates this with CIFAR-10 plain-net curves at depths
20 and 56, where the deeper network trains worse, not just tests worse.

**Why it's a real problem, not just an ImageNet leaderboard question**: if depth-induced
degradation is an optimization failure rather than an overfitting or representational
limit, then a large class of "just make it deeper" approaches are dead-ended until
something addresses that failure directly — this is what motivates ruling out vanishing
gradients and longer training before proposing a reformulation (N04, N05, N06).
