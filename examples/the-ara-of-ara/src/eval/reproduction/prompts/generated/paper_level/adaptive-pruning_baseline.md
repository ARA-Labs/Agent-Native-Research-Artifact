# Full Paper Reproduction: adaptive-pruning

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/adaptive-pruning_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/adaptive-pruning_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/adaptive-pruning.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/adaptive-pruning` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/adaptive-pruning_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Set up the infrastructure for reproducing APT: load RoBERTa-base and T5-base (t5-lm-adapt) into memory, set up data pipelines for SST2 and MNLI (GLUE), SQuAD 2.0, and CNN/DailyMail, implement evaluation metrics (dev accuracy for SST2/MNLI, dev F1 for SQuAD, ROUGE 1/2/L for CNN/DM), and implement efficiency measurement utilities (97% time-to-accuracy, peak GPU memory via torch.cuda.max_memory_allocated, inference throughput, inference memory). Set up LoRA so it can be applied to transformer modules and merged before inference. [easy]

**Success criteria:**

1. **[9ad77547]** (weight=1) Code has been implemented such that RoBERTa can be loaded into memory
2. **[fa5309a4]** (weight=1) Code has been implemented such that T5, specifically t5-lm-adapt, can be loaded into memory
3. **[c9daa9ee]** (weight=1) Code for accessing the train and dev splits from the SST2 dataset from the GLUE benchmark has been implemented
4. **[5fef034a]** (weight=1) Code for accessing the train and dev splits from the MNLI dataset from the GLUE benchmark has been implemented
5. **[8605df37]** (weight=1) Code for accessing the train and dev splits from the SQuAD 2.0 benchmark has been implemented
6. **[4e1da193]** (weight=1) Code for accessing the train and test sets from the CNN Dailymail (CNN/DM) dataset has been implemented
7. **[1fdb66d7]** (weight=1) When evaluating models on SST2 and MNLI, the dev set accuracy is reported
8. **[d43a1c9e]** (weight=1) When evaluating models on SQuAD, the dev set F1 score is reported
9. **[698b1e1c]** (weight=1) When evaluating models on CNN/DM, the ROUGE 1/2/L scores on the test set are reported
10. **[3aeea066]** (weight=1) For each method trained on some dataset, the train time is measured as the time-to-accuracy of reaching [X]% of the dev (/test) set performance of the finetuning baseline
11. **[79a20612]** (weight=1) For each method, when being trained on some dataset, code has been implemented to record the max GPU memory utilization, using torch.cuda.max_memory_allocated() (or equivalent)
12. **[240b99e2]** (weight=1) For each method, when being evaluated on some dataset, the speed of inference is measured as the inference throughput (sampled processed per second)
13. **[1ff3dcb3]** (weight=1) For each method, when performing inference with some dataset, code has been implemented to record the max GPU memory utilization, using torch.cuda.max_memory_allocated() (or equivalent)
14. **[48e1cbcb]** (weight=1) LoRA is available to be applied to modules within transformers
15. **[d5ec9b1a]** (weight=1) After training a method using LoRA adapters, before performing inference, the LoRA parameters are merged into the parameters of the model

### Subtask 2 of 10: Implement the APT adapter architecture (Section 4.1) for RoBERTa-base. The APT adapter extends LoRA by adding learnable binary pruning masks on both input (m_i) and output (m_o) dimensions, a frozen original weight matrix W, and two learnable low-rank matrices W_A (r_apt x d_i) and W_B (d_o x r_apt) whose rank r_apt can vary dynamically per layer. The forward pass computes (W + 2 * W_B * W_A) applied to the masked input (X * m_i), with the result masked by m_o. When applied to MHA layers, m_i prunes the hidden dimension and m_o prunes attention heads; for FFN layers, m_i prunes the hidden dimension and m_o prunes internal neurons. Attach APT adapters to query/value projections in MHA and the up-projection in FFN layers. APT parameters must be merged before inference. [easy]

**Success criteria:**

1. **[b16c44c6]** (weight=1) The masked input to the APT adapter is computed as $X \circ m_i$, where $X$ is the input to the adapter and is $m_i \in \mathbb{R}^d_i$ a learnable binary pruning mask
2. **[a1686474]** (weight=1) When APT is applied to MHA layers, $m_i$ prunes the transformers' hidden dimension
3. **[169a5eb2]** (weight=1) When APT is applied to FFN layers, $m_i$ prunes the transformers' hidden dimension
4. **[3a628b4e]** (weight=1) For the APT adapter implementation, a dynamic rank $r_{apt}$ is defined for each weight matrix, which can vary
5. **[18060c53]** (weight=1) For the APT adapter implementation, a new learnable weight matrix $W_A \in \mathbb{R}^{r_{apt} \times d_i}$ is defined
6. **[ee70fcc6]** (weight=1) For the APT adapter implementation, a new learnable weight matrix $W_B \in \mathbb{R}^{d_o \times r_{apt}}$ is defined
7. **[c99479b2]** (weight=1) For the APT adapter implementation, the original weight matrix $W$ is kept frozen; it isn't updated during training
8. **[bf86efe4]** (weight=1) For the APT adapter implementation, the new weight matrix is computed as $W + 2 \cdot W_B W_A$
9. **[bb7ec9df]** (weight=1) For the APT adapter implementation, the new weight matrix is multipled by the masked input
10. **[5f68b482]** (weight=1) For the APT adapter implementation, the output of the multiplication between the updated weights and masked input is masked by a learnable binary pruning mask $m_o \mathbb{R}^d_o$
11. **[9500d7e2]** (weight=1) When the APT adapter is applied to MHA layers, $m_o$ prunes attention heads
12. **[472390c9]** (weight=1) When the APT adapter is applied to FFN layers, $m_o$ prunes internal neurons in the FFN layers
13. **[ca6ea57b]** (weight=1) After training a model using APT adapters, before performing inference, the APT parameters are merged into the parameters of the model
14. **[dde4b5f2]** (weight=1) LoRA and APT adapters are added to queries and values of MHA layers in RoBERTa and T5
15. **[2a3669df]** (weight=1) LoRA and APT adapters are added to the up layer in FFN layers in RoBERTa and T5

### Subtask 3 of 10: Implement all baseline methods for RoBERTa-base: (1) Fine-tuning (FT) baseline by full fine-tuning a pre-trained model; (2) LoRA+Prune baseline by first adding LoRA adapters, fine-tuning, then applying Mask Tuning (from retraining-free-pruning); (3) Prune+Distill baseline using CoFi (from CoFiPruning); (4) LoRA+Prune+Distill baseline using CoFi pruning and distillation with LoRA parameters only, where only L_0 modules and LoRA parameters are tunable. Configure dataset-specific hyperparameters: lr 2e-4 for GLUE/SQuAD, 1e-4 for CNN/DM; batch size 32 for GLUE/SQuAD, 16 for CNN/DM; 40 epochs for GLUE/SQuAD (non-FT), 16 for CNN/DM (non-FT); FT baseline 10 epochs; initial APT rank 8. [easy]

**Success criteria:**

1. **[3ec70bbe]** (weight=1) The fine-tuning baseline is implemented by finetuning a pre-trained model on a dataset
2. **[791e26f6]** (weight=2) The Mask Tuning baseline is implemented, using the implementation at https://github.com/WoosukKwon/retraining-free-pruning
3. **[c4790fad]** (weight=1) In LoRA+Prune, LoRA adapters are first added to modules of the given model
4. **[e2236b08]** (weight=1) In LoRA+Prune, the model with the LoRA adapters added is finetuned
5. **[95d71d15]** (weight=1) In LoRA+Prune, once the model with LoRA adapters has finished finetuning, Mask Tuning is applied to the model
6. **[1ad3cbb6]** (weight=2) The CoFi baseline (also named "Prune+Distill" in Section 5.2) is implemented, using the implementation at https://github.com/princeton-nlp/CoFiPruning
7. **[92a96898]** (weight=1) In LoRA+Prune+Distill, LoRA adapters are first added to modules of the given model
8. **[a7b5b5ae]** (weight=1) In LoRA+Prune+Distill, CoFi pruning and distillation is used but with LoRA parameters only; only the $L_0$ modules (the non-negative stochastic gates in CoFi which collectively determine which weights to set to zero) and LoRA parameters are tuneable
9. **[e193b120]** (weight=1) All models trained on GLUEuse a learning rate of 2e-4
10. **[83a476b8]** (weight=1) All models trained on GLUEuse a batch size of 32
11. **[d441dc31]** (weight=1) For every method that isn't Finetune, models trained on GLUE use 40 epochs
12. **[452a6371]** (weight=1) The Finetune method is trained for 10 epochs
13. **[6287838a]** (weight=1) The adapter ranks $r_{apt}$ in all APT modules are initialized to 8

### Subtask 4 of 10: Reproduce the ablation study (Section 5.6, Table 4) on RoBERTa-base at 60% sparsity. Run three ablation variants: (1) APT w/o adaptive pruning (w/o A_P) on SST2 and MNLI, verifying ~94 SST2, ~[X] MNLI, [X]% faster training than FT, [X]% of FT memory; (2) APT w/o adaptive tuning (w/o A_T) on SST2 and MNLI, verifying ~93 SST2, ~84 MNLI, similar to LoRA+Prune performance, [X]% slower convergence than full APT; (3) APT w/o self-distillation (w/o D_S), verifying [X]% faster training time and [X]% less memory than full APT. Also run APT on RoBERTa at sparsities 40%-95% on SST2/MNLI for the Pareto analysis, and compute relative accuracy vs the FT baseline. Verify APT dominates LoRA+Prune on the Pareto frontier ([X]% faster inference, [X]% less memory at matched accuracy for RoBERTa). [medium]

**Success criteria:**

1. **[e9fa1766]** (weight=1) RoBERTa is trained and evaluated on SST2 and MNLI separately with 60% sparsity using a modified version of APT that doesn't use adaptive pruning (APT w/o $A_P$)
2. **[7525718b]** (weight=1) The recorded metrics show that when pruning with APT w/o $A_P$, the task performance of RoBERTa reaches roughly 94 for SST2 and 87.5 for MNLI
3. **[16db85a1]** (weight=1) The recorded metrics show that when pruning with APT w/o $A_P$, the RoBERTA training speed with APT w/o $A_P$ is roughly 20% faster than full fine-tuning on the same datasets
4. **[66039c65]** (weight=1) The recorded metrics show that when pruning with APT w/o $A_P$, the RoBERTA training using APT w/o $A_P$ requires roughly 60% of the memory compared to full fine-tuning on the same datasets
5. **[859bffed]** (weight=1) RoBERTa is trained using a modified version of APT that doesn't use adaptive tuning (APT w/o $A_T$) using 60% sparsity
6. **[011cf2f5]** (weight=1) The recorded metrics show that when pruning RoBERTa with APT w/o $A_T$, it achieves roughly 93 on SST2
7. **[1a57a576]** (weight=1) The recorded metrics show that when pruning RoBERTa with APT w/o $A_T$, it achieves roughly 84 on MNLI
8. **[26fbd16f]** (weight=1) The recorded metrics show that when pruning RoBERTa with APT w/o $A_T$, it has a similar performance as the LoRA+Prune baseline
9. **[70a1b6da]** (weight=1) The recorded metrics show that when pruning RoBERTa with APT w/o $A_T$, it converged roughly 15% slower than full APT
10. **[e7ad0e1d]** (weight=1) RoBERTa is trained using 60% sparsity and a modified version of APT that doesn't use self-distillation (APT w/o $D_S$)
11. **[10f451dd]** (weight=1) The recorded metrics show that pruning RoBERTa with APT w/o $D_S$ has roughly 20% faster training time than full APT
12. **[9c90df0a]** (weight=1) The recorded metrics show that pruning RoBERTa with APT w/o $D_S$ costs roughly 10% less training memory than full APT
13. **[5a92263e]** (weight=1) RoBERTa with the APT method is trained and evaluated on SST2 and MNLI separately for sparsities 40%, 50%, 60%, 70%, 80%, 90%, 95%, and the relative is computed using the average on SST2 and MNLI
14. **[d406c635]** (weight=1) RoBERTa with the LoRA+Prune, LoRA+Prune+Distill, and Prune+Distill methods is trained and evaluated on SST2 and MNLI separately, and the relative performance is computed using the average on SST2 and MNLI

### Subtask 5 of 10: Implement the outlier-aware salience scoring and low-cost adaptive pruning algorithm (Sections 4.2, Appendix B). For non-adapter parameters, salience is |W_{i,j} * dL/dW_{i,j}|; for APT adapter layers, salience follows Equation 9. The outlier-aware salience augments base salience with sqrt(kurtosis) of the activation. Maintain an exponential moving average of salience (coefficient 0.85). Implement block parameter counting (MHA head = 4*d_m*d_m/n_h, FFN neuron = 2*d_m, hidden dimension = n_L*(4*d_m + 2*n_f)), salience density (salience / param count), and block category function f. Implement the binary search procedure to select top-i blocks by salience density, and decrease pruned blocks' masks by 0.01. Implement the cubic sparsity schedule gamma_t = gamma_T + (1 - gamma_T)(1 - t/T)^3. [medium]

**Success criteria:**

1. **[56fadbbe]** (weight=1) For a parameter $W_{i,j}$ that is not in an APT adapter layer, the salience is computed as $S(W_{i,j}) = \left| W_{i,j} \cdot \frac{\partial \mathcal{L}}{\partial W_{i,j}} \right|$
2. **[67496368]** (weight=1) For an APT adapter layer, the salience is computed following equation 9 as the sum of the block-wise frozen weight salience and the corresponding tuning weight
3. **[7f8d2c8b]** (weight=1) Outlier-aware salience for a block is computed as $\hat{S}(W_{:,j}) = \tilde{S}(W_{:,j}) + \left( \text{Kurt}(O_{j,:}) \right)^{\frac{1}{2}}$, where $\tilde{S}$ is the salience score, $O_{:,j} = W_{:,j} \circ X_{j,:}^T$ represents the activation, and $\text{Kurt}(\cdot)$ stands for Kurtosis
4. **[6c5119f5]** (weight=1) During training, the outlier-aware salience of each block is computed as an exponential moving-average $\overline{S}^{(t)}(m) \gets 0.85 \overline{S}^{(t-1)}(m) + 0.15 \hat{S}(m)$, where $\overline{S}^{(t)}(m)$ is the moving-average of block $m$ at time step $t$, and $\hat{S}(m)$ is the current outlier-aware salience score of block $m$
5. **[293d6fac]** (weight=1) Given a hidden dimensionality $d_m$ and number of attention heads $n_h$, the number of parameters of a MHA head is computed as $4 \times d_m \times d_m / n_h$
6. **[4a6f0dfe]** (weight=1) Given a hidden dimensionality $d_m$, the number of parameters of a FFN neuron is computed as $2 \times d_m$
7. **[87383bb6]** (weight=1) Given a hidden dimensionality $d_m$, number of layers $n_L$, and number of neurons in the FFN layer $n_f$, the number of parameters associated with a transformers hidden dimension across all layers is computed as $n_L \times (4 d_m + 2 n_f)$
8. **[1d80f3a3]** (weight=1) For a block with salience $S$ and number of parameters $\mathcal{C}$, the salience density is computed as the salience divided by the parameter number $S / \mathcal{C}$
9. **[a3ae8772]** (weight=1) The salience density is only calculated for blocks that have an APT adapter applied to them
10. **[8e4cb47d]** (weight=1) The salience density of each block is re-computed everytime the number of parameters of the model changes
11. **[4221dd78]** (weight=1) The blocks are sorted by their salience density in descending order
12. **[50d7ad1a]** (weight=1) A function $f$ for identifying a block's category is implemented, following equation 13. $f$ returns 0 when block $b_i$ is a head, 1 if $b_i$ is a neuron, and 2 if $b_i$ is a dimension
13. **[c32d372a]** (weight=1) Following equation 14, given any index $i$ and a sorted list of N blocks in descending order of salience density, the number of blocks in the top-$i$ blocks that are added to heads is computed as $n_h^\prime = \sum_{j=0}^{i-1} \delta (0, f(b_j))$, where $\delta (i, j)$ is the Kronecker delta function that returns 1 if $i=j$, and otherwise 0, and $f$ is the function that returns 0 when block $b_i$ is a head, 1 if $b_i$ is a neuron, and 2 if $b_i$ is a dimension
14. **[7de18cb9]** (weight=1) Following equation 14, given any index $i$ and a sorted list of N blocks in descending order of salience density, the number of blocks in the top-$i$ blocks that are added to neurons is computed as $n_f^\prime = \sum_{j=0}^{i-1} \delta (1, f(b_j))$, where $\delta (i, j)$ is the Kronecker delta function that returns 1 if $i=j$, and otherwise 0, and $f$ is the function that returns 0 when block $b_i$ is a head, 1 if $b_i$ is a neuron, and 2 if $b_i$ is a dimension
15. **[256c6f16]** (weight=1) Following equation 14, given any index $i$ and a sorted list of N blocks in descending order of salience density, the number of blocks in the top-$i$ blocks that are added to dimensions is computed as $d_m^\prime = \sum_{j=0}^{i-1} \delta (2, f(b_j))$, where $\delta (i, j)$ is the Kronecker delta function that returns 1 if $i=j$, and otherwise 0, and $f$ is the function that returns 0 when block $b_i$ is a head, 1 if $b_i$ is a neuron, and 2 if $b_i$ is a dimension

### Subtask 6 of 10: Implement the adaptive tuning mechanism (Section 4.3) and integrate it with the pruning algorithm. Compute adapter importance I(H_apt) = sum of W_B salience scores, sort adapters by importance, and linearly increase the rank of the top-half adapters by concatenating Gaussian-initialized rows to W_A and zero rows to W_B. Implement the remaining pruning algorithm components: the top-i parameter count computation following Equation 14 (C_top-i = (4*d_h'*n_h' + 2*n_f')*d_m'), and binary search for block selection. Verify that mask updates (decrease by 0.01 for pruned blocks) work correctly in conjunction with rank updates. [medium]

**Success criteria:**

1. **[664da958]** (weight=1) In Adaptive and Efficient LM Tuning, given an APT adapter $H_{apt}$, the importance score is computed as $\mathcal{I}(H_{apt}) = \sum_{i,j} S(W_{Bi,j})$, the summation of the parameter salience scores in $W_B$ (where $W_B \in \mathbb{R}^{d_o \times r_{apt}}$ is an APT tuning parameter)
2. **[7fd4d11b]** (weight=1) In Adaptive and Efficient LM Tuning, APT adapters are sorted by their importance score
3. **[0e3baed9]** (weight=1) When increasing tuning parameter from $\Delta t$ to $Delta t^{\prime}$, the salient layer's rank is changed from $r_{apt}$ to $r_{apt}^\prime=\lfloor{r_{apt} \cdot \frac{\Delta_t^\prime}{\Delta_t }\rfloor$
4. **[48d8285a]** (weight=1) When adding parameters, random Gaussian initialized parameters $\mathcal{N}(0, \sigma^2)$ are concatenated to $W_A$, and zeros are concatenated to $W_B$, where $W_A \in \mathbb{R}^{r_{apt} \times d_i}$,  $W_B \in \mathbb{R}^{d_o \times r_{apt}}$ are both APT tuning parameters
5. **[d3dcd793]** (weight=1) Following equation 14, given any index $i$ and a sorted list of N blocks in descending order of salience density, the parameter number is computed as $C_{\text{top}-i} = (4d_h^\prime \cdot n_h^\prime + 2n_f^\prime) \cdot d_m^\prime$, where $d_h^\prime$ is the number of heads in the model, $n_h^\prime$ is the number of the top-$i$ blocks that are added to heads, $n_f^\prime$ is the number of the top-$i$ blocks that are added to neurons, and $d_m^\prime$ is the number of the top-$i$ blocks that are added to dimensions
6. **[b424b0fc]** (weight=1) In Low-cost Adaptive LM Pruning, binary search is used to get the top-$i$ salient blocks
7. **[215e9429]** (weight=1) In Low-cost Adaptive LM Pruning, blocks that are marked to be pruned have their corresponding masks decreased by 0.01
8. **[50acfee7]** (weight=1) When pruning LMs with APT, given a pre-determined target sparsity $\gamma_T$ and total number of pruning training steps $T$, the target sparsity at timestep $t$ is computed by $\gamma_t = \gamma_T + (1 - \gamma_T) \left(1 - \frac{t}{T}\right)^3$

### Subtask 7 of 10: Implement efficient self-knowledge distillation (Section 4.4) and configure the two-phase training pipeline. Self-distillation randomly samples 4 teacher layers (one per quarter slice), dynamically maps them to the closest non-pruned student layers via MSE with a learnable linear transform (initialized as identity), and re-computes the mapping every step. The distillation loss combines layer-wise MSE (L_layer) with KL-divergence on output logits (L_pred), weighted 0.9*L_layer + L_pred for GLUE and 0.9*L_layer + 0.1*L_pred for SQuAD/CNN-DM. A linearly ramping mu blends L_distill with supervised fine-tuning loss. Configure the two-phase schedule: first prune+distill (20 epochs GLUE/SQuAD, 6 epochs CNN/DM), then fine-tune (20 epochs GLUE/SQuAD, 10 epochs CNN/DM). [medium]

**Success criteria:**

1. **[2b494437]** (weight=1) In Efficient Self-Knowledge Distillation, at each training epoch, intermediate layers from the teacher model are randomly selected for distillation; 4 teacher layers are randomly sampled in each quarter slice of the layers (e.g. for a 12-layer network the slices would be: 0-2, 3-5, 6-8, 9-11)
2. **[92744e38]** (weight=1) In Efficient Self-Knowledge Distillation, the teacher-student layer-mapping function $m(\cdot)$ is implemented to match 4 teacher layers with the closest, non-pruned student layers, using the same method introduced in CoFi (Xia et al., 2022). For each of the 4 teacher layers, the layer mapping function dynamically determines which of the student layers is closest; $\mathop{\arg \min}\limits_{j:\mathbf{z}_{FFN}^{(j)}>0} \text{MSE} (W_{\text{layer}} H_s^j, H_t^i)$, where $H_s^j, H_t^i$ are hidden representations from the $j$-th student FFN layer and $i$-th teacher layer respectively, and $W_{\text{layer}} \in \mathbb{R}^{d\timesd}$ is a learnable linear transformation matrix, initialized as an identity matrix
3. **[39282784]** (weight=1) In Efficient Self-Knowledge Distillation, the teacher-student layer-mapping function $m(\cdot)$ is re-computed every training step
4. **[28658a50]** (weight=1) In Efficient Self-Knowledge Distillation, the hidden layer distillation loss is defined as $\mathcal{L}_{\text{layer}} = \sum_{i=1}^4 \text{MSE}(\text{Tr}(H_s^{\phi(i)}), H_t^i)$, where $\text{Tr}$ denotes the tunable LoRA layer for layer transformation, initialized as an identical matrix $\mathcal{I}$, and $\phi(\cdot)$ is the teacher-student layer-mapping function
5. **[4b5df1a0]** (weight=1) In Efficient Self-Knowledge Distillation, $\mu$ is a moving term that linearly scales from 0 to 1 during pruning
6. **[8f4b756f]** (weight=1) In Efficient Self-Knowledge Distillation, cross-entropy loss between the pruned student's and teacher's output probability distributions $\mathbf{p}_s$ and $\mathbf{p}_t$ is computed as $\mathcal{L}_{\text{pred}} = D_{\text{KL}}(\mathbf{p}_s \,\|\, \mathbf{p}_t)$
7. **[1e6df51c]** (weight=1) In Efficient Self-Knowledge Distillation, when training on GLUE tasks, the layer distillation is combined with the prediction-layer distillation: $\mathcal{L}_{\text{distill}} = \mathcal{L}_{\text{pred}} + 0.9 \mathcal{L}_{\text{layer}}$
8. **[16f88c2e]** (weight=1) In Efficient Self-Knowledge Distillation, when training on SQuAD or CNN/DM, the layer distillation is combined with the prediction-layer distillation: $\mathcal{L}_{\text{distill}} = 0.1 \mathcal{L}_{\text{pred}} + 0.9 \mathcal{L}_{\text{layer}}$
9. **[3f534396]** (weight=1) Following equation 7, the distillation objective is defined as $\mathcal{L} = \mu \mathcal{L}_{\text{distill}} + (1 - \mu) \mathcal{L}_{\text{ft}}$, where $\mathcal{L}_{ft}$ is the supervised fine-tuning objective
10. **[43b7fa8c]** (weight=1) When pruning LMs with APT, the LM is first pruned and trained with the self-distillation objective for some pre-defined number of epochs, then it is fine-tuned on the same dataset for some other pre-defined number of epochs
11. **[fe34b5f1]** (weight=1) When training on the GLUE dataset using the Prune+Distill, LoRA+Prune+Distill, or APT methods, the first 20 epochs are used for distillation, and the remaining 20 are for training on the objective
12. **[a5c6d56b]** (weight=1) When training on the SQuAD dataset using the Prune+Distill, LoRA+Prune+Distill, or APT methods, the first 20 epochs are used for distillation, and the remaining 20 are for training on the objective
13. **[908deb8d]** (weight=1) When training on the CNN/DM dataset using the Prune+Distill, LoRA+Prune+Distill, or APT methods, the first 6 epochs are used for distillation, and the remaining 10 are for training on the objective

### Subtask 8 of 10: Train and evaluate RoBERTa-base with APT and all baselines (FT, LoRA, LoRA+Prune, Prune+Distill, LoRA+Prune+Distill) at 60% sparsity on SST2 and MNLI. Report dev accuracy for each method on both tasks. Use GLUE hyperparameters: lr 2e-4, batch size 32, 40 epochs (20+20 for distillation methods), FT 10 epochs. Verify that: (1) APT achieves equal or higher task performance than LoRA+Prune on both SST2 and MNLI, (2) APT has similar task accuracy to Prune+Distill, and (3) APT achieves better task performance than LoRA+Prune+Distill. [hard]

**Success criteria:**

1. **[01d90251]** (weight=1) RoBERTa with the FT, LoRA, LoRA+Prune, and APT methods is trained and evaluated on MNLI, SST2, and SQuAD v2 separately with 60% sparsity
2. **[8e9dce7a]** (weight=1) RoBERTa with the Prune+Distill and LoRA+Prune+Distill methods is trained and evaluated on MNLI and SST2 separately with 60% sparsity.
3. **[cdcbff81]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT achieves an equal or higher performance than LoRA+Prune across all evaluations
4. **[ec378300]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT has similar task accuracy to Prune+Distill across MNLI and SST2
5. **[e1fe1c33]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT achieves better task performance than LoRA+Prune+Distill
6. **[9662eaea]** (weight=1) All models trained on SQuAD use a learning rate of 2e-4
7. **[89b01087]** (weight=1) All models trained on SQuAD use a batch size of 32
8. **[c99c524a]** (weight=1) For every method that isn't Finetune, models trained on SQuAD use 40 epochs

### Subtask 9 of 10: Measure and compare efficiency metrics for RoBERTa-base at 60% sparsity across APT, LoRA+Prune, Prune+Distill, and LoRA+Prune+Distill on SST2/MNLI. Measure: 97% time-to-accuracy (training convergence speed), peak GPU training memory, inference throughput, and inference memory. Verify that: (1) APT converges ~8x faster than LoRA+Prune, (2) APT uses similar GPU memory as LoRA+Prune during training and inference, (3) APT costs [X]% of Prune+Distill's training memory and converges 2.5x faster, and (4) APT requires less training time and memory than LoRA+Prune+Distill. [hard]

**Success criteria:**

1. **[d075f77c]** (weight=1) The recorded metrics show that when pruning RoBERTa to 60% sparsity, APT converged about 8x faster than the LoRA+Prune baseline
2. **[be593611]** (weight=1) The recorded metrics show that when pruning RoBERTa to 60% sparsity, APT used similar GPU memory during both training and inference compared to the LoRA+Prune baseline
3. **[37612400]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT costs roughly 40% of training memory compared to Prune+Distill
4. **[9f477ec1]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT converges 2.5x faster than Prune+Distill
5. **[dc200210]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT requires less training time than LoRA+Prune+Distill
6. **[5a2b6715]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, APT requires less memory than LoRA+Prune+Distill
7. **[939d1034]** (weight=1) The recorded metrics indicate that APT is about 20% faster in inference than the LoRA+Prune baseline for RoBERTa, when comparing the APT model that achieved the closest accuracy to the LoRA+Prune baseline
8. **[00ce14bb]** (weight=1) The recorded metrics indicate that APT is about 7% more memory efficient than the LoRA+Prune baseline for RoBERTa, when comparing the APT model that achieved the closest accuracy to the LoRA+Prune baseline

### Subtask 10 of 10: Train and evaluate T5-base (t5-lm-adapt) with APT, FT, LoRA, and LoRA+Prune at 60% sparsity on SST2 and CNN/DM. Use dataset-specific hyperparameters: lr 2e-4/batch 32/40 epochs for SST2; lr 1e-4/batch 16/16 epochs (6+10 for APT) for CNN/DM. Report dev accuracy for SST2, ROUGE 1/2/L for CNN/DM, plus efficiency metrics (training time, training memory, inference throughput, inference memory). Verify that: (1) APT converges ~8x faster than LoRA+Prune for T5, (2) APT uses similar GPU memory as LoRA+Prune, (3) APT has [X]% better end-task performance than LoRA+Prune on average, (4) APT's inference efficiency is slightly worse than LoRA+Prune on T5, and (5) compute the relative accuracy metric for the Pareto analysis. [hard]

**Success criteria:**

1. **[dcc716d8]** (weight=1) T5 with the FT, LoRA, LoRA+Prune, and APT methods is trained and evaluated on MNLI, SST2, and CNN/DM separately with 60% sparsity
2. **[7fb47445]** (weight=1) The recorded metrics show that when pruning T5 to 60% sparsity, APT converged about 8x faster than the LoRA+Prune baseline
3. **[c6179a9c]** (weight=1) The recorded metrics show that when pruning T5 to 60% sparsity, APT used similar GPU memory during both training and inference compared to the LoRA+Prune baseline
4. **[de57690a]** (weight=1) The recorded metrics show that when pruning T5 under 60% sparsity, APT has roughly 5% better end-task performance on average than the LoRA+Prune baseline
5. **[737f8df7]** (weight=1) The recorded metrics show that when pruning T5 under 60% sparsity, the inference efficiency reached by APT is worse than the LoRA+Prune baseline
6. **[fbdc9a9e]** (weight=1) The recorded metrics show that when pruning RoBERTa and T5 to 60% sparsity, the inference efficiency reached by APT is about the same as the LoRA+Prune baseline
7. **[e32c3c58]** (weight=1) All models trained on CNN/DM use a learning rate of 1e-4
8. **[2fff2695]** (weight=1) All models trained on CNN/DM use a batch size of 16
9. **[f0f7160e]** (weight=1) For every method that isn't Finetune, models trained on CNN/DM use 16 epochs
10. **[93cb26c7]** (weight=1) The recorded metrics indicate that APT is about 60% faster in inference than the LoRA+Prune baseline for T5, when comparing the APT model that achieved the closest accuracy to the LoRA+Prune baseline
11. **[b7607af8]** (weight=1) The recorded metrics indicate that APT is about 25% more memory efficient than the LoRA+Prune baseline for T5, when comparing the APT model that achieved the closest accuracy to the LoRA+Prune baseline
12. **[0c47a836]** (weight=1) For Section 5.5, the relative accuracy for some model is computed as the accuracy such model achieves when compared to the accuracy the finetuning baseline achieves
13. **[24223a79]** (weight=1) T5 with the LoRA+Prune method is trained and evaluated on SST2 and MNLI separately, and the relative performance is computed using the average on SST2 and MNLI
14. **[8df3184f]** (weight=1) T5 with the APT method is trained and evaluated on SST2 and MNLI separately for sparsities 40%, 50%, 60%, 70%, 80%, 90%, and the relative performance is computed using the average on SST2 and MNLI

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/adaptive-pruning_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: adaptive-pruning

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
