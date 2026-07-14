# Full Paper Reproduction: self-expansion

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-expansion_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-expansion_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/self-expansion.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/self-expansion` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-expansion_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Reproduce the expansion threshold sensitivity analysis (Section 4.3, Figure 3). Train SEMA with expansion thresholds from 1.0 to 2.0 (in 0.1 increments) on ImageNet-A, and from 1.0 to 2.0 (in 0.1 increments) on VTAB. For each threshold, record the final average accuracy and the number of adapters in each of the last three transformer layers. Verify: (a) accuracy remains stable across threshold range [1.0, 2.0] on ImageNet-A, (b) adapter count decreases monotonically as threshold increases, (c) VTAB accuracy is higher with low thresholds than with high thresholds. [easy]

**Success criteria:**

1. **[e416a999]** (weight=1) Code is implemented to count the number of adapters added to each of the last three transformer layers
2. **[bb921111]** (weight=1) SEMA is separately trained with expansion thresholds 1.0, 1.1, 1.2, ...., 2.0 on ImageNet-A
3. **[9254bba9]** (weight=1) For each SEMA model trained with a different expansion threshold, the average accuracy at the end of training on the ImageNet-A dataset has been computed using the test split at the end of each task
4. **[2d255c7d]** (weight=1) For each SEMA model trained with a different expansion threshold on ImageNet-A, the number of adapters at the end of training in each of the last three layers is computed
5. **[1a82caf9]** (weight=1) SEMA is separately trained with expansion thresholds 1.0, 1.1, 1.2, ...., 2.0 on VTAB
6. **[9e2e9c35]** (weight=1) For each SEMA model trained with a different expansion threshold, the average accuracy at the end of training on the VTAB dataset has been computed using the test split at the end of each task
7. **[db0f6083]** (weight=1) For each SEMA model trained with a different expansion threshold on VTAB, the number of adapters at the end of training in each of the last three layers is computed
8. **[cac935d6]** (weight=1) The recorded metrics show that the average accuracy of the SEMA models trained on ImageNet-A does not significantly vary over expansion thresholds 1.0, 1.1, 1.2, ...., 2.0
9. **[b1205f44]** (weight=1) The recorded metrics show that the incremental accuracy of the SEMA models trained on ImageNet-A does not significantly vary over expansion thresholds 1.0, 1.1, 1.2, ...., 2.0
10. **[a50983cd]** (weight=1) The recorded metrics show that the SEMA models trained on ImageNet-A have more adapters when trained with lower expansion thresholds then when they are trained with higher expansion thresholds
11. **[a302cd1d]** (weight=1) The recorded metrics show that the average accuracy of the SEMA models trained on VTAB is higher with low expansion thresholds (1.0, 2.0) than high expansion thresholds (7.0, 8.0)
12. **[e9857488]** (weight=1) The recorded metrics show that the incremental accuracy of the SEMA models trained on VTAB is higher with low expansion thresholds (1.0, 2.0) than high expansion thresholds (7.0, 8.0)
13. **[d91d9aa5]** (weight=1) The recorded metrics show that the SEMA models trained on VTAB have more adapters when trained with lower expansion thresholds then when they are trained with higher expansion thresholds

### Subtask 2 of 10: Reproduce the dynamic expansion process analysis and adapter usage analysis (Section 4.3, Figures 4 and 5). Train SEMA on VTAB (5 tasks) with self-expansion limited to the final transformer layer only, logging per-batch reconstruction error from each representation descriptor. Verify: (a) each descriptor's reconstruction loss decreases during training and oscillates around a stable value, (b) reconstruction loss spikes during the detection phase at the start of each new task, (c) exactly 3 descriptors are present after all 5 tasks, (d) no new descriptors are added during tasks 4 and 5. Compute adapter usage by averaging routing weight vectors from test-set samples per task and normalizing. Verify first 3 adapters dominate their introducing tasks, task 4 reuses adapter 1, and task 5 reuses adapter 3. [easy]

**Success criteria:**

1. **[c35a2668]** (weight=1) For the SEMA model trained for the experiment in in Section 4.3 on "Analysis on dynamic expansion process", self-expansion is limited to the final layer of the transformer
2. **[8e458cfa]** (weight=1) For the SEMA model trained in Section 4.3 on "Analysis on dynamic expansion process", the reconstruction error from each representation descriptor is recorded for each batch
3. **[30c33054]** (weight=1) The modified SEMA model for Section 4.3 on "Analysis on dynamic expansion process" is trained on the first five tasks from the VTAB dataset
4. **[22377755]** (weight=1) The recorded metrics show that, during training, each representation descriptor's reconstruction loss lowers over the course of training, and eventually oscillates around some value
5. **[4c514efc]** (weight=1) The recorded metrics show that, during the detection phase at the start of each task, the reconstruction loss increases for each present representation descriptor that was introduced in the previous task
6. **[afdd1870]** (weight=1) The recorded metrics show that in total three representation descriptors are present in the final model after training
7. **[041c37ec]** (weight=1) The recorded metrics show that no representation descriptors were added during the final two tasks
8. **[8e1377c2]** (weight=1) Using the model trained in Section 4.3 on "Analysis on dynamic expansion process", the adapter usage for each task has been computed by averaging the routing weight vectors from all samples seen in tasks in the test set, then normalizing the final result such that the sum of average weights for each task sums to one
9. **[4e89af61]** (weight=1) The recorded metrics show that, the first adapter has a large usage for the first task, the second adapter has a large usage for the second task, and the third adapter has a large usage for the third task
10. **[3dc20642]** (weight=1) The recorded metrics show that, the fourth task uses the first adapter; the first adapter has the largest usage for the fourth task
11. **[88dcf9d6]** (weight=1) The recorded metrics show that, the fifth task uses the third adapter; the thirs adapter has the largest usage for the fifth task

### Subtask 3 of 10: Reproduce the multi-layer expansion analysis (Section 4.3, Table 4) and the adapter variant comparison (Section 4.3, Table 3). For multi-layer: train SEMA on ImageNet-A and VTAB with varying numbers of expansion-eligible layers (last 2, last 3, last 4). Verify that more expansion-eligible layers yields higher accuracy and more adapters. For adapter variants: implement LoRA and Convpass adapters as drop-in replacements, train SEMA with each adapter type (Adapter, LoRA, Convpass) on ImageNet-A and VTAB, and verify all variants achieve competitive accuracy within [X]% of each other. [easy]

**Success criteria:**

1. **[df30022a]** (weight=1) A variant of SEMA is trained on ImageNet-A where the only layers allowed for self-expansion are 11-12 (the last 2 layers)
2. **[0a1ec651]** (weight=1) A variant of SEMA is trained on ImageNet-A where the only layers allowed for self-expansion are 10-12 (the last 3 layers)
3. **[1fac6183]** (weight=1) A variant of SEMA is trained on ImageNet-A where the only layers allowed for self-expansion are 9-12 (the last 4 layers)
4. **[7960f0dc]** (weight=1) For each SEMA variant trained on ImageNet-A allowing different layers for self-expansion, the average accuracy at the end of training has been computed using the test split at the end of each task
5. **[14696e47]** (weight=1) The recorded metrics show that the average accuracy of SEMA trained on ImageNet-A is higher when layers 9-12 are allowed for self-expansion compared to when only layers 11-12 are allowed for self-expansion
6. **[bf0ca018]** (weight=1) The recorded metrics show that the average accuracy of SEMA trained on VTAB is higher when layers 9-12 are allowed for self-expansion compared to when only layers 11-12 are allowed for self-expansion
7. **[2fc5dc38]** (weight=1) The LoRA adapter can be applied (it is either implemented or an existing implementation is imported)
8. **[7fa8715e]** (weight=1) The Convpass adapter architecture has been implemented from https://github.com/JieShibo/PETL-ViT/blob/main/convpass/vtab/convpass.py and can be selected as the functional adapter
9. **[e0aa0321]** (weight=1) The ADAM "adapter" is implemented from https://github.com/ShoufaChen/AdaptFormer/blob/main/models/adapter.py
10. **[6329ed8e]** (weight=1) The recorded metrics show that for each dataset (ImageNet-A, VTAB) all models trained on such dataset have similar average accuracies and incremental accuracies (<4%)
11. **[4a7122fc]** (weight=1) The recorded metrics show that all models trained on the ImageNet-A dataset achieve an average accuracy >50% and an incremental accuracy >60%
12. **[5ca4eec8]** (weight=1) The recorded metrics show that all models trained on the VTAB dataset achieve an average accuracy >85% and an incremental accuracy >88%

### Subtask 4 of 10: Implement the baseline methods for continual learning comparison: Finetune Adapter (single adapter per layer, continual fine-tuning with frozen ViT), L2P, DualPrompt, CODA-P (all from LAMDA-PILOT repo), SimpleCIL (from RevisitingCIL repo), and ADAM with Adapter (from RevisitingCIL repo). Configure all baselines with proper hyperparameters from Section 4.1: SGD optimizer, lr=0.005 for adapters, lr=0.01 for descriptors, cosine annealing, batch size 32, 5 epochs for adapters, 20 epochs for descriptors. [medium]

**Success criteria:**

1. **[821e4ced]** (weight=1) The Finetune Adapter baseline is implemented by adding one SEMA adapter to each of all layers in the frozen ViT
2. **[213fe0b4]** (weight=1) The Finetune Adapter baseline is trained by continually fine-tuning the SEMA adapters throughout all tasks in the task stream encountered during training
3. **[033c6646]** (weight=1) When training the Finetune Adapter baseline, the backbone ViT is frozen and only the (parameters of the) adapters are updated continually by all tasks
4. **[2522988f]** (weight=1) L2P has been implemented, using the implementation available within this repo: https://github.com/sun-hailong/LAMDA-PILOT
5. **[e40c9f90]** (weight=1) DualPrompt has been implemented, using the implementation available within this repo: https://github.com/sun-hailong/LAMDA-PILOT
6. **[65005d38]** (weight=1) CODA-P has been implemented, using the implementation available within this repo: https://github.com/sun-hailong/LAMDA-PILOT
7. **[258321d1]** (weight=1) SimpleCIL has been implemented, using the official implementation at https://github.com/zhoudw-zdw/RevisitingCIL
8. **[897aae5d]** (weight=1) ADAM with Adapter has been implemented, using the official implementation at https://github.com/zhoudw-zdw/RevisitingCIL
9. **[06cd5080]** (weight=1) All adapters are trained for 5 epochs.
10. **[256cc0e7]** (weight=1) The representation descriptors are trained for 20 epochs.
11. **[4b60235a]** (weight=1) The batch size is 32.
12. **[5ecb2fba]** (weight=1) SGD is used as the optimizer.
13. **[81f71ca5]** (weight=1) The initial learning rate is set to 0.005 for adapters.
14. **[ed1f909f]** (weight=1) The initial learning rate is set to 0.01 for representational descriptors.
15. **[3be032fb]** (weight=1) The learning rate decays with cosine annealing.

### Subtask 5 of 10: Train and evaluate SEMA and all baselines (Finetune Adapter, L2P, DualPrompt, CODA-P, SimpleCIL, ADAM) on ImageNet-A and VTAB. For each method on each dataset, compute the average accuracy after all tasks and the average incremental accuracy. Verify that SEMA achieves the highest or near-highest accuracy and incremental accuracy across methods and throughout training, confirming the main claim of the paper (Section 4.2, Table 1). [medium]

**Success criteria:**

1. **[13236aed]** (weight=1) The Finetune Adapter baseline has been trained on the ImageNet-A dataset
2. **[16c22564]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of the Finetune Adapter baseline during training on the ImageNet-A dataset has been computed using the test split
3. **[0a7f5caf]** (weight=1) The Finetune Adapter baseline has been trained on the VTAB dataset
4. **[9a243585]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of the Finetune Adapter baseline during training on the VTAB dataset has been computed using the test split
5. **[cd6d6a59]** (weight=1) SEMA has been trained on the ImageNet-A dataset
6. **[8f54e2fe]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of SEMA during training on the ImageNet-A dataset has been computed using the test split
7. **[ace39db2]** (weight=1) The incremental accuracy of SEMA during training on the ImageNet-A dataset has been computed using the test split at the end of each task
8. **[1dfccd39]** (weight=1) SEMA has been trained on the VTAB dataset
9. **[40ac1b84]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of SEMA during training on the VTAB dataset has been computed using the test split
10. **[bb23038c]** (weight=1) The incremental accuracy of SEMA during training on the VTAB dataset has been computed using the test split at the end of each task
11. **[fd1aa6e8]** (weight=1) The recorded metrics show that the average accuracy of SEMA is almost always higher than that of the other methods for all the datasets.
12. **[5392a57b]** (weight=1) The recorded metrics show that the average incremental accuracy of SEMA at the end of training is almost always higher than that of the other methods for all the datasets.
13. **[f88415b6]** (weight=1) The recorded metrics show that the average incremental accuracy of SEMA throughout training is almost always higher than that of the other methods, when comparing to methods trained on the same dataset for the same number of tasks

### Subtask 6 of 10: Train and evaluate the remaining ablation routing variants (Average Weighting, Random Weighting, Top-1 Selection, Random Selection, Top-1 Selection Inference) on both ImageNet-A and VTAB (Section 4.3, Table 2). For each variant on each dataset, compute average accuracy and incremental accuracy after all tasks. This completes the full ablation table by providing execution results for all routing strategy variants. [medium]

**Success criteria:**

1. **[135f6fdc]** (weight=1) The architecture variant "Average Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
2. **[f7de59e1]** (weight=1) Using the architecture variant "Average Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing", the average accuracy (of all seen tasks after training on all tasks) during training on the ImageNet-A dataset has been computed using the test split
3. **[1bc09532]** (weight=1) The architecture variant "Average Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB
4. **[50cb9235]** (weight=1) Using the architecture variant "Average Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing", the average accuracy (of all seen tasks after training on all tasks) during training on the VTAB dataset has been computed using the test split
5. **[1d30f56d]** (weight=1) The architecture variant "Random Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
6. **[1325a4b3]** (weight=1) The architecture variant "Random Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB
7. **[4f01fac3]** (weight=1) The architecture variant "Top-1 Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
8. **[8c9ebd55]** (weight=1) The architecture variant "Top-1 Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB
9. **[70e161eb]** (weight=1) The architecture variant "Random Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
10. **[6bd258ed]** (weight=1) The architecture variant "Random Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB
11. **[0cf9f0b3]** (weight=1) The architecture variant "Top-1 Selection Inference" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
12. **[7bf23f28]** (weight=1) The architecture variant "Top-1 Selection Inference" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB

### Subtask 7 of 10: Implement the SEMA architecture components: functional adapter (down-projection, ReLU, up-projection), representation descriptor (linear encoder to 128 dims, LeakyReLU, linear decoder), and router (learnable linear mapping + softmax). Integrate these into a frozen ViT-B/16-IN1K backbone so that the output of the second normalization layer feeds the adapters, descriptors, and router, and the weighted adapter mixture is added as a residual to the FC-layer + residual output of the transformer block. Implement the combined cross-entropy + reconstruction loss. Set up the CIFAR-100 and ImageNet-R datasets with proper class-incremental splits (10 classes per task). [hard]

**Success criteria:**

1. **[5b88aaa9]** (weight=1) Code has been implemented such that a ViT-B/16 model pretrained on ImageNet-1K can be loaded into memory
2. **[3aabf7f3]** (weight=1) The train and test sets of CIFAR-100 are available
3. **[3964f08d]** (weight=1) The train and test sets of of ImageNet-R are available
4. **[638c80be]** (weight=1) Datasets (CIFAR-100, ImageNet_R, ImageNet-A) are split in a manner where each task/domain consists of 10 distinct classes
5. **[dc0de847]** (weight=1) The functional adapter has been implemented correctly as described in Section 3.3, as a learnable down projection layer, then a ReLU function, then a learnable up projection layer
6. **[2da70bdf]** (weight=1) The encoder of the representation descriptor is implemented as a linear layer that projects to 128 dimensions
7. **[6c7fab21]** (weight=1) LeakyReLU is applied to the output of the encoder of the representation descriptor
8. **[f76f7de8]** (weight=1) The decoder of the representation descriptor is implemented as a linear layer that projects from 128 dimensions back to the original dimensionality
9. **[b990c55b]** (weight=1) The router has been implemented as a linear mapping function (using a learnable matrix) followed by a softmax operation
10. **[c1e41bb2]** (weight=1) The output of the second normalization layer (after the first normalization layer, then multi-head self-attention, then residual connection) is used as input for the representation descriptors, functional adapters, and router
11. **[8f70800b]** (weight=1) A linear combination of the outputs of the functional adapters is computed, with the weights corresponding to the output of the router
12. **[7cf18f2c]** (weight=1) A linear combination of the outputs of the functional adapters is added to the output of the fully connected layer and the residual layer in the transformer block to produce the output for the transformer layer
13. **[061cf57d]** (weight=1) For training SEMA, the loss of the model $F$ is implemented correctly; given an input-label pair $(x, y)$, the cross entropy loss between the output of the model $F(x)$ and $y$ is computed
14. **[5b0fa5b0]** (weight=1) For training SEMA, the reconstruction loss for the representation descriptors is implemented correctly; given an input $x$ to the representation descriptor $g$, the loss is computed as the 2-norm of the difference between the input and output; $||x - g(x)||_2^2$
15. **[7c152eab]** (weight=1) For training SEMA, the overall loss given an input-label pair $(x, y)$ is computed as the cross-entropy loss of the output of the network with the label $y$ and the sum of reconstruction losses of all representation descriptors across all layers

### Subtask 8 of 10: Implement the SEMA training loop: z-score-based expansion decision logic (running statistics over 500 samples, scanning layers shallowest-to-deepest), the freeze/unfreeze protocol when new adapters are added (new adapter learnable, all others frozen; new descriptor learnable, others frozen; new router weights learnable, others frozen), and classification head expansion for new classes. Set up ImageNet-A and VTAB datasets with proper splits. Use the specified hyperparameters: SGD optimizer, lr=0.005 for adapters, lr=0.01 for descriptors, cosine annealing, batch size 32, 5 epochs for adapters, 20 epochs for descriptors, self-expansion in last 3 layers, adapter bottleneck dim 48. Implement the average accuracy and average incremental accuracy metrics. [hard]

**Success criteria:**

1. **[b4553344]** (weight=1) The train and test sets of ImageNet-A are available
2. **[f727d425]** (weight=1) The train and test sets of VTAB are available. The VTAB dataset used is the VTAB subset from the ADAM paper; only five domains are used, and the domain order is fixed to "resisc45 10-19; dtd 20-29; pets 30-39; eurosat 40-49; flowers 50-59". Only 10 classes are selected and used for each domain; the numbers denote the class index of the 10 classes for each domain. For example, 10-19 denotes the 10th - 19th classes are in resisc are used. The original resisc contains 45 classes.
3. **[505dd960]** (weight=1) When training SEMA, the parameters of the pretrained model (e.g. ViT) are frozen.
4. **[186e1f6a]** (weight=1) When training SEMA, the running statistics of the mean and standard deviation of the reconstruction error are stored for each representation descriptor, using the previous 500 samples (over all tasks) that were used for training prior to the current sample
5. **[85768b74]** (weight=1) When training SEMA, the z-score corresponding to the $k$-th representation descriptor in layer $l$ can be computed as $z_k^l = (r_k^l - u_k^l)/\sigma_k^l$, where $r_k^l$ is the reconstruction error of the current input, $u_k^l$ is the associated running mean of the representation descriptor, and $\sigma_k^l$ is the associated running standard deviation of the representation descriptor
6. **[3345ee1d]** (weight=1) When training SEMA on the $t$-th task, before starting any training, the layers that are valid for expansion are scanned iteratively for evaluating whether layers should have adapters added, from shallowest to deepest
7. **[4b3a8b1d]** (weight=1) When training SEMA on the $t$-th task, when scanning each layer the reconstruction error is computed over all samples in the $t$-th task. No training occurs during this scanning, and no gradients are computed
8. **[ddf48454]** (weight=1) When training SEMA on the $t$-th task, when scanning each layer, if after some sample, all the z-scores of all the representation descriptors on some layer are above some pre-defined threshold, an expansion signal is triggered for such layer, and an adapter is added to such layer and trained on the task $t$. After training on the task $t$, the next deepest layer is scanned. If no deeper layer exists, the training proceeds to the next task, and the scanning restarts from the first (valid) layer
9. **[ac81c23b]** (weight=1) When training SEMA on the $t$-th task, when scanning each layer, if no expansion signals are triggered, the task is skipped (no training is performed for such task and no adapters are added), and all existing functional adapters and representation descriptors are frozen
10. **[f3854228]** (weight=1) When training SEMA, when adding a new adapter, the weights in the new adapter are learnable, and all the weights in the other adapters in all other layers are frozen.
11. **[2d34ab6a]** (weight=1) When training SEMA, when adding a new adapter, the weights in the representation descriptor corresponding to the new adapter are learnable, and all the other weights in the other representation descriptors are frozen.
12. **[ede350f7]** (weight=1) When training SEMA, when adding a new adapter, the weights in the router corresponding to the new adapter are learnable parameters, and all the other weights in the router are frozen.
13. **[9aeec6b6]** (weight=1) When a new task is added, the classification head has been expanded to handle the new classes
14. **[9b147fe2]** (weight=1) The average accuracy $A_N$ of all seen tasks after training on the $N$-th task, is computed as $A_N = \frac{1}{N} \sum_{i=1}^N A_{i,N}$, where $A_{i,N}$ is the accuracy of the $i$-th task after training on the $N$-th task
15. **[db420a9d]** (weight=1) The average incremental accuracy $\bar{A}$ is computed as $\bar{A} = \frac{1}{N} \sum_{t=1}^N A_t$, where $A_t$ is the average accuracy on all seen tasks after training on the $t$-th task

### Subtask 9 of 10: Train and evaluate SEMA and all baselines (Finetune Adapter, L2P, DualPrompt, CODA-P, SimpleCIL, ADAM) on CIFAR-100 and ImageNet-R. For each method on each dataset, compute the average accuracy after all tasks and the average incremental accuracy. Verify that SEMA achieves the highest or near-highest accuracy on both datasets. [hard]

**Success criteria:**

1. **[192d5f0a]** (weight=1) The Finetune Adapter baseline has been trained on the CIFAR-100 dataset
2. **[26ae9c3c]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of the Finetune Adapter baseline during training on the CIFAR-100 dataset has been computed using the test split
3. **[69a418f5]** (weight=1) The Finetune Adapter baseline has been trained on the ImageNet-R dataset
4. **[d4e485c4]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of the Finetune Adapter baseline during training on the ImageNet-R dataset has been computed using the test split
5. **[e8a269ed]** (weight=1) The L2P baseline has been trained on the CIFAR-100 dataset
6. **[05874696]** (weight=1) The L2P baseline has been trained on the ImageNet-R dataset
7. **[2bc9441f]** (weight=1) SEMA has been trained on the CIFAR-100 dataset
8. **[dc6a493b]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of SEMA during training on the CIFAR-100 dataset has been computed using the test split
9. **[cdc7db5a]** (weight=1) The incremental accuracy of SEMA during training on the CIFAR-100 dataset has been computed using the test split at the end of each task
10. **[765a25a3]** (weight=1) SEMA has been trained on the ImageNet-R dataset
11. **[13629fa4]** (weight=1) The average accuracy (of all seen tasks after training on all tasks) of SEMA during training on the ImageNet-R dataset has been computed using the test split
12. **[6d2442b9]** (weight=1) The incremental accuracy of SEMA during training on the ImageNet-R dataset has been computed using the test split at the end of each task

### Subtask 10 of 10: Implement the six ablation variants for the expansion/routing study (Section 4.3, Table 2): (1) No Expansion (single adapter, no expansion after task 1), (2) Average Weighting (uniform router weights), (3) Random Weighting (random weights per sample), (4) Top-1 Selection (hardmax at train and inference), (5) Random Selection (random single adapter per sample), (6) Top-1 Selection at Inference only (soft mixture training, hardmax inference). Train the No Expansion variant plus full SEMA on ImageNet-A and VTAB, and verify that SEMA outperforms all variants overall while Top-1 Inference is second-best. [hard]

**Success criteria:**

1. **[f4446727]** (weight=1) The architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is a variant of SEMA that has one adapter per layer of the transformer
2. **[3ebfcc70]** (weight=1) The architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" does not add adapters during training, i.e., there is no self-expansion
3. **[55756009]** (weight=1) The architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" does train the adapters after the first task
4. **[952bbc57]** (weight=1) The architecture variant "Average Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is implemented as a variant of the SEMA architecture that uses an average weighting of the outputs of the functional adapters (e.g. the router has the same weight for each adapter)
5. **[a5959da9]** (weight=1) The architecture variant "Random Weighting" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is implemented as a variant of the SEMA architecture that uses a linear combination (from random weights) of the outputs of the functional adapters (e.g. the router has random weights for each adapter), where the random weights are re-computed per-sample
6. **[4eed6ff6]** (weight=1) The architecture variant "Top-1 Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is implemented as a variant of the SEMA architecture that only uses the output of the single adapter that has the highest weight from the router during both training and inference
7. **[aecc19c4]** (weight=1) The architecture variant "Random Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is implemented as a variant of the SEMA architecture that only uses the output of the single adapter chosen at random, where the adapter that is randomly chosen is re-computed (randomly) per-sample
8. **[02c22ec6]** (weight=1) The architecture variant "Top-1 Selection" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" is implemented as a variant of the SEMA architecture that uses the standard SEMA method during training, but during inference only uses the output of the single adapter that has the highest router weight
9. **[ef33c6a5]** (weight=1) The architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on ImageNet-A
10. **[960373b2]** (weight=1) Using the architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing", the average accuracy (of all seen tasks after training on all tasks) during training on the ImageNet-A dataset has been computed using the test split
11. **[5e45d561]** (weight=1) The architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing" has been trained on VTAB
12. **[8f05eab2]** (weight=1) Using the architecture variant "No Expansion" introduced in Section 4.3 on "Ablation studies on module expansion and adapter composing", the average accuracy (of all seen tasks after training on all tasks) during training on the VTAB dataset has been computed using the test split
13. **[4d764fd4]** (weight=1) The recorded metrics show that SEMA achieves about equal or higher performance wrt. incremental accuracy and average accuracy on both the ImageNet-A and VTAB datasets
14. **[32f0f139]** (weight=1) The recorded metrics show that the Top-1 Selection Inference variant achieves about equal or higher performance wrt. incremental accuracy and average accuracy on both the ImageNet-A and VTAB datasets compared to all other variants (but not compared to SEMA)

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-expansion_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: self-expansion

## Subtask 1 of 10: {goal}
### Setup
What you installed, configured, prepared
### Implementation
Key code and design decisions
### Results
Actual numerical outputs
### Self-Assessment
For each requirement: met / partially met / not met, with justification
### Issues
Problems encountered, if any

## Subtask 2 of 10: {goal}
...
(repeat for each subtask attempted)
```

## Critical Rules

- **Do NOT fabricate results.** If code fails to run, report the failure. If a metric cannot be computed, say so. Inventing numbers is worse than reporting a failure.
- **Do NOT hardcode expected values.** Your results must come from actually running the experiment, not from copying numbers you found in the source material.
- **Hardware constraint**: Assume you have access to a single GPU (A100 80GB). If a subtask requires more, implement a reduced-scale version and document the difference.
- **Time constraint**: Target <= 8 GPU-hours per subtask. If full training is infeasible, run a shortened version and document the reduction.
- **Cumulative work**: Reuse code, models, and data from earlier subtasks. Do not redo setup work unnecessarily.
