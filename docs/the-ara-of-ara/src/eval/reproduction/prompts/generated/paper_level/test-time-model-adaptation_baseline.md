# Full Paper Reproduction: test-time-model-adaptation

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/test-time-model-adaptation_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/test-time-model-adaptation_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/test-time-model-adaptation.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/test-time-model-adaptation` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/test-time-model-adaptation_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the FOA core infrastructure: load a pretrained ViT-Base from timm, obtain the ImageNet-1K and ImageNet-C datasets, implement the fitness function (Equation 5) combining prediction entropy and activation distribution discrepancy, compute and store source domain statistics, implement the CMA-ES prompt optimizer with population sampling and parameter updates, implement the back-to-source activation shifting mechanism with EMA direction updates (Equations 7-9), and implement accuracy and ECE metrics. This is a pure implementation task with no evaluation runs required. [easy]

**Success criteria:**

1. **[vit-base]** (weight=1) Code has been implemented such that a ViT-Base model pre-trained on ImageNet-1K can be loaded into memory using the timm repository
2. **[07ab27df]** (weight=1) The ImageNet-1K dataset is obtained.
3. **[e66011b0]** (weight=1) The ImageNet-C dataset is obtained, which contains corrupted images in 15 types and 5 severity levels for each type.
4. **[new-uuid]** (weight=1) A mechanism is implemented to calculate and store the source domain statistics (mean and standard deviation) of the N-th layer's CLS token features, computed over a set of source training samples.
5. **[prompt-i]** (weight=1) The input prompt mechanism is implemented to add learnable prompts to the inputs following the required arrangement: [CLS token, learnable prompts, patch embeddings].
6. **[dd2b0167]** (weight=1) For each $x \in X_t$, the term $\sum_{c \in C} -\hat{y}_c \log \hat{y}_c$ is computed, where $X_t$ is the current batch of test samples, $C$ is the set of all classes, and $\hat{y}_c$ is the predicted probability for class c
7. **[94f30003]** (weight=1) The above expression ($\sum_{c \in C} -\hat{y}_c \log \hat{y}_c$) is summed over all $x \in X_t$.
8. **[cdd126eb]** (weight=1) The difference in means is computed correctly, as the sum over $x \in X_t$ of $\lambda * ||\mu_i(X_t) - \mu_i^S|| _2$.
9. **[4c1b3e06]** (weight=1) The difference in standard deviations is computed correctly, as the sum over $x \in X_t$ of $||\sigma_i(X_t) - \sigma_i^S||_2$.
10. **[new-uuid]** (weight=1) The total fitness value is computed correctly by summing all components: the entropy term over X_t and all activation discrepancy terms (means and standard deviations).
11. **[8cc7f4ee]** (weight=1) Given a population size K, the t-th prompt $p^{(t)}_k$ is sampled K times i.i.d. (k=1,...,K) via $p^{(t)}_k \sim m^{(t)} + \tau^{(t)} \mathcal{N}(0, \sigma^{(t)})$, where $m^{(t)}$ is the mean vector, $\tau^{(t)}$ is the step size, and $\sigma^{(t)}$ is the covariance matrix at iteration t.
12. **[6fce355f]** (weight=1) Each prompt p^{(t)}_k is concatenated with the embeddings of test batch X_t as input to the model, producing fitness values v_k. These K fitness values are then used to update the parameters via the CMA algorithm.
13. **[source-s]** (weight=1) A mechanism is implemented to calculate and store the source domain statistics (mean and standard deviation) of the N-th layer's CLS token features, computed over a set of source training samples.
14. **[45191ae5]** (weight=1) Classification accuracy on OOD examples is implemented correctly.
15. **[3487990e]** (weight=1) ECE (expected calibration error), the difference between predicted probabilities and actual outcomes in a probabilistic model, is implemented correctly.

### Subtask 2 of 10: Implement the activation shifting mechanism details and set all FOA hyperparameters correctly. This includes: batch-mean computation, EMA update rule, shifting direction calculation, gamma-scaled CLS feature shift, correct initialization of the moving average from the first batch, and all default parameter values (Np=3, uniform init, BS=64, K=28, lambda=0.4/0.2, alpha=0.1, gamma=1.0, 32-bit precision, full ImageNet-1K val for source stats). Verify source statistics are computed and stored. [easy]

**Success criteria:**

1. **[dfa8753b]** (weight=1) For each batch of elements $X_t$, the mean of the elements is computed as $\mu_N(X_t)$.
2. **[6ae1951a]** (weight=1) For each batch of elements $X_t$, an update is made as $\mu_N(t) = \alpha * \mu_N(X_t) + (1 - \alpha) * \mu_N(t-1)$, where $\alpha$ is a configurable hyperparameter.
3. **[37a2aa82]** (weight=1) The shifting direction $d_t$ is set to $\mu^S_N - \mu_N(t)$, where $\mu^S_N$ is the mean of the $N$-th final layer CLS feature calculated over source in-distribution samples $\mathcal{D}_S$.
4. **[88178132]** (weight=1) To shift the output of the OOD data points from the t-th batch to match the in-distribution domain, $\gamma * d_t$ is added to the $N$-th layer's CLS feature $e^0_N$, where gamma is a configurable hyperparameter.
5. **[activati]** (weight=1) The activation shifting moving average muN(0) is correctly initialized using the statistics of the first batch muN(X1).
6. **[96fe6dab]** (weight=1) The number of prompt embeddings N_p is set to 3.
7. **[0c2acf08]** (weight=1) Prompts are initialized uniformly.
8. **[c33f98df]** (weight=1) The batch size (BS) is set to 64.
9. **[bc867c99]** (weight=1) The population size K is set to 28.
10. **[69c93e10]** (weight=1) Lambda is set to 0.4 on ImageNet-C/V2/Sketch
11. **[03d22003]** (weight=1) Lambda is set to 0.2 on ImageNet-R
12. **[7bf85e71]** (weight=1) For activation shifting, alpha is set to 0.1.
13. **[38ece210]** (weight=1) The step size gamma for activation shifting is set to 1.0.
14. **[new-uuid]** (weight=1) The model precision is set to 32-bits by default unless otherwise specified.
15. **[new-uuid]** (weight=1) The full ImageNet-1K validation set is used for computing source statistics.

### Subtask 3 of 10: Implement all baseline TTA methods with their prescribed hyperparameters. Implement gradient-free baselines: LAME (BS=64, k=5) and T3A (BS=64, M=20). Implement gradient-based baselines: TENT (BS=64, SGD, momentum=0.9, lr=0.001), CoTTA (SGD, momentum=0.9, lr=0.05, BS=64, p_th=0.1, 32 augmentations, restoration prob=0.01, EMA alpha=0.999), and SAR (SGD, momentum=0.9, lr=0.001, BS=64, entropy threshold=0.4*ln(C), trainable params=blocks1-8 LN affine). This is a pure implementation task. [easy]

**Success criteria:**

1. **[lame-imp]** (weight=1) The LAME baseline is implemented from https://github.com/fiveai/LAME
2. **[t3a-impl]** (weight=1) The T3A baseline is implemented from https://github.com/matsuolab/T3A
3. **[tent-imp]** (weight=1) The TENT baseline is implemented from https://github.com/DequanWang/tent
4. **[cotta-im]** (weight=1) The CoTTA baseline is implemented from https://github.com/qinenergy/cotta
5. **[sar-impl]** (weight=1) The SAR baseline is implemented from https://github.com/mr-eggplant/SAR
6. **[656e67f1]** (weight=1) LAME uses a batch size of 64
7. **[537a4b4a]** (weight=1) For the kNN affinity matrix in LAME, $k=5$
8. **[955216ec]** (weight=1) T3A uses a batch size of 64
9. **[12e08875]** (weight=1) In T3A, the number of supports to restore $M$ is set to 20
10. **[caabc6a0]** (weight=1) TENT uses a batch size of 64
11. **[4402b969]** (weight=1) TENT uses SGD as the update rule
12. **[ccc0dd8a]** (weight=1) TENT uses a momentum of 0.9
13. **[df17b005]** (weight=1) TENT uses a learning rate of 0.001
14. **[2500492e]** (weight=1) SAR uses SGD as its optimizer
15. **[891b9f8e]** (weight=1) SAR uses momentum=0.9

### Subtask 4 of 10: Evaluate all methods on ImageNet-C (severity 5, all 15 corruptions) with full-precision 32-bit ViT-Base (Tables 2 and 16). Run NoAdapt, LAME, T3A, TENT, CoTTA, SAR, and FOA. Verify: FOA achieves highest average accuracy and lowest average ECE; LAME and T3A perform at or below NoAdapt; gradient-based methods outperform gradient-free ones; FOA exceeds SAR by 2-6% in both accuracy and ECE; FOA ECE is >10pp lower than TENT. [medium]

**Success criteria:**

1. **[a3892035]** (weight=1) The accuracies on all 15 corruptions are calculated for the baseline methods (NoAdapt, LAME, T3A).
2. **[09a51455]** (weight=1) The ECE scores on all 15 corruptions are calculated for the baseline methods (NoAdapt, LAME, T3A).
3. **[dd10692c]** (weight=1) The accuracies on all 15 corruptions are calculated for the gradient-based methods (TENT, CoTTA, SAR) and FOA.
4. **[413cecbd]** (weight=1) The ECE scores on all 15 corruptions are calculated for the gradient-based methods (TENT, CoTTA, SAR) and FOA.
5. **[806d13f1]** (weight=1) FOA has a higher average accuracy score than all other methods.
6. **[f49179f6]** (weight=1) FOA has a lower average ECE score than all other methods.
7. **[14e863e3]** (weight=1) LAME and T3A perform around the same or worse than NoAdapt both on average accuracy and on average ECE.
8. **[e358b89e]** (weight=1) TENT, CoTTA, and SAR have higher average accuracy than the gradient-free methods (LAME and T3A).
9. **[e008e8e1]** (weight=1) Compared to SAR, the average accuracy of FOA is 2-6% higher.
10. **[564653b0]** (weight=1) Compared to SAR, the average ECE of FOA is 2-6% lower.
11. **[fa981c83]** (weight=1) FOA's ECE score is more than [X]% lower than that of TENT.
12. **[new-uuid]** (weight=1) The statistics $\{\mu^S_i, \sigma^S_i\}^N_{i=0}$ are computed and stored for use in FOA.
13. **[fb2c9926]** (weight=1) SAR uses a learning rate of 0.001
14. **[95ba7d30]** (weight=1) In SAR the entropy threshold is $E_0$ is set to $0.4\\times\\ln C$, where $C$ is the number of task classes
15. **[87cca796]** (weight=1) In SAR the trainable parameters are the affine parameters of the layer normalization modules from blocks1 to blocks8 for ViT-Base

### Subtask 5 of 10: Evaluate all methods on ImageNet-R (lambda=0.2), ImageNet-V2, and ImageNet-Sketch (Table 3). Obtain these three datasets. Evaluate gradient-free baselines (NoAdapt, LAME, T3A) and gradient-based methods (TENT, CoTTA, SAR) alongside FOA on all 3 benchmarks for both accuracy and ECE. Verify FOA achieves comparable or highest accuracy and comparable or lowest ECE across these distribution shift benchmarks. [medium]

**Success criteria:**

1. **[imagenet]** (weight=1) The ImageNet-R dataset containing artistic renditions of 200 ImageNet classes is obtained
2. **[imagenet]** (weight=1) The ImageNet-V2 matched frequency subset dataset is obtained
3. **[imagenet]** (weight=1) The ImageNet-Sketch dataset containing black and white sketches is obtained
4. **[91f4fde3]** (weight=1) The accuracies on all 3 benchmarks are calculated for the baseline methods (NoAdapt, LAME, T3A).
5. **[76d49374]** (weight=1) The ECE scores on all 3 benchmarks are calculated for the baseline methods (NoAdapt, LAME, T3A).
6. **[b384d1f5]** (weight=1) The accuracies on all 3 benchmarks are calculated for the gradient-based methods (TENT, CoTTA, SAR).
7. **[e337c8f0]** (weight=1) The ECE scores on all 3 benchmarks are calculated for the gradient-based methods (TENT, CoTTA, SAR).
8. **[0ee5fada]** (weight=1) The average accuracy value of FOA is comparable or higher than the average accuracy values of the other methods.
9. **[6613dcf6]** (weight=1) The average ECE value of FOA is comparable or lower than the average ECE values of the other methods.

### Subtask 6 of 10: Reproduce the FOA component ablation study (Table 5). Run FOA with all 7 component subsets of {entropy fitness, activation discrepancy fitness, activation shifting} on all 15 ImageNet-C corruptions (severity 5). Compute average accuracy and ECE for each configuration. Verify: entropy-only CMA collapses below NoAdapt; activation discrepancy alone gives >5% accuracy gain over NoAdapt; activation shifting alone gives >2% accuracy gain over NoAdapt; full combination achieves best accuracy; full combination achieves best ECE. [medium]

**Success criteria:**

1. **[44021325]** (weight=1) FOA is trained for all subsets of the following three components on ImageNet-C: 1) The entropy term in the fitness function, 2) The activation discrepepancy term in the fitness function, 3) Use of activation shifting.
2. **[c6a02904]** (weight=1) The average accuracy and ECE score is computed over all 15 corruptions of ImageNet-C on all the runs of FOA.
3. **[8c734773]** (weight=1) CMA with Entropy fitness performs poorer than NoAdapt.
4. **[4c40bfda]** (weight=1) Using Activation Discrepancy fitness causes a > 5 % increase in accuracy compared to NoAdapt.
5. **[60c1e713]** (weight=1) Using only activation shifting causes a > 2 % increase in accuracy compared to NoAdapt
6. **[ec71c4f7]** (weight=1) When combining all three components, the accuracy is comparable to or higher than all other component combinations
7. **[f0373fea]** (weight=1) When combining all three components, the ECE score is comparable to or lower than all other component combinations.

### Subtask 7 of 10: Reproduce the design choice study (Table 9) and the population size sensitivity analysis (Figure 2a). Implement norm-layer-only and prompt-only training modes, SGD and CMA optimizers, entropy and fitness (Eq.5) loss functions. Run the design choice grid on ImageNet-C Gaussian noise (severity 5). Verify: CMA+entropy on norm layers collapses near 0.1% accuracy; prompts+CMA+fitness is effective; SGD+fitness on norm layers exceeds TENT by >8%. Sweep population size K from 2-28 on ImageNet-C Gaussian noise. Verify: K=2 beats T3A and NoAdapt, K=6 matches TENT, accuracy converges past K=15. [hard]

**Success criteria:**

1. **[norm-lay]** (weight=1) Code is implemented to allow training only the normalization layer parameters of ViT-Base while keeping other parameters frozen
2. **[prompt-t]** (weight=1) Code is implemented to allow training only the input prompt parameters while keeping the ViT-Base model parameters frozen
3. **[sgd-impl]** (weight=1) SGD optimizer is implemented with momentum of 0.9 and configurable learning rate
4. **[cma-impl]** (weight=1) CMA optimizer is implemented with configurable population size and step size
5. **[entropy-]** (weight=1) Entropy minimization loss is implemented for test-time adaptation
6. **[fitness-]** (weight=1) The fitness function from Equation 5 combining entropy and activation discrepancy is implemented
7. **[componen]** (weight=1) The model is trained with different learnable parameters (norm layers only vs prompts only) and the accuracy scores and ECE scores are computed
8. **[optimize]** (weight=1) The model is trained with different optimizers (SGD vs CMA) and the accuracy scores and ECE scores are computed
9. **[loss-exp]** (weight=1) The model is trained with different loss functions (entropy vs fitness from equation 5) and the accuracy scores and ECE scores are computed
10. **[cma-entr]** (weight=1) Direct replacement of SGD with CMA for entropy-based TTA is shown to be infeasible (accuracy degrading to a smaller percentage on the order of 0.1%).
11. **[prompt-e]** (weight=1) Using prompts with CMA and the devised fitness function achieves effective performance.
12. **[sgd-fitn]** (weight=1) The proposed fitness function (Eqn. 5) achieves excellent performance even with SGD learning, showing significant improvement (> [X]% increase in average accuracy) compared to TENT with entropy loss.
13. **[7cf9ca07]** (weight=1) FOA is trained with population sizes K equal to 2, 3, ..., 28, on the Gaussian corrputed samples from ImageNet-C.
14. **[ee156450]** (weight=1) The accuracy and ECE values are computed for the above values of K, both on FOA and on NoAdapt, on the Gaussian noise corrupted samples from ImageNet-C (severity level 5).
15. **[7a05f97c]** (weight=1) At K = 2, FOA outperforms NoAdapt and T3A in accuracy.

### Subtask 8 of 10: Reproduce the remaining hyperparameter sensitivity analyses (K convergence, Np stability, Q stability) and the quantized model evaluation (Table 4). Verify K convergence past 15 and K=6 matching TENT. Sweep Np from 1-10 and verify accuracy/ECE stability. Sweep Q from 16-1600 and verify stability past Q=32. Create 8-bit and 6-bit ViT-Base models via PTQ4ViT with 32 calibration samples. Evaluate NoAdapt, T3A, and FOA on both quantized models across all 15 ImageNet-C corruptions (severity 5). Verify FOA outperforms T3A on both precision levels and 8-bit FOA exceeds full-precision TENT by >2%. [hard]

**Success criteria:**

1. **[46befbf5]** (weight=1) At K = 6, FOA is comparable to or is better than TENT in accuracy.
2. **[b4b1643c]** (weight=1) The accuracy of FOA converges as K goes past 15.
3. **[6f98319e]** (weight=1) FOA is trained with N_p values equal to 1, 2, ..., 10, on the Gaussian corrputed samples from ImageNet-C.
4. **[be075650]** (weight=1) The accuracy and ECE values are computed for the above values of N_p, both on FOA and on NoAdapt, , on the Gaussian noise corrupted samples from ImageNet-C (severity level 5).
5. **[25d31a1a]** (weight=2) The accuracy only makes minor variations across different values of N_p.
6. **[51f85c1f]** (weight=2) The ECE only maks minor variations across different values of N_p.
7. **[126f14d6]** (weight=1) FOA is trained with Q values equal to 16, 32, 64, 100, 200, 400, 800, 1600, where Q is the number of source training samples used for calculating the source statistics, on the Gaussian corrupted samples from ImageNet-C.
8. **[1e18930c]** (weight=1) The accuracy and ECE values are computed for the above values of Q, both on FOA and on NoAdapt, , on the Gaussian noise corrupted samples from ImageNet-C (severity level 5).
9. **[684701d0]** (weight=2) The accuracy is stable when Q goes past 32.
10. **[4a0dce24]** (weight=2) The ECE is stable when Q goes past 32.
11. **[quantize]** (weight=1) Quantized 8-bit and 6-bit ViT-Base models are created using PTQ4ViT, using 32 randomly selected training samples from the ImageNet-1K training set as training data
12. **[8bit-acc]** (weight=1) The accuracies on all 15 corruptions are calculated for the methods (NoAdapt, T3A, and FOA) using 8-bit quantized ViT
13. **[8bit-ece]** (weight=1) The ECE scores on all 15 corruptions are calculated for the methods (NoAdapt, T3A, and FOA) using 8-bit quantized ViT
14. **[6bit-acc]** (weight=1) The accuracies on all 15 corruptions are calculated for the methods (NoAdapt, T3A, and FOA) using 6-bit quantized ViT
15. **[6bit-ece]** (weight=1) The ECE scores on all 15 corruptions are calculated for the methods (NoAdapt, T3A, and FOA) using 6-bit quantized ViT

### Subtask 9 of 10: Reproduce the memory/compute efficiency analysis (Tables 6-8) and single-sample FOA-I adaptation experiments. Implement FOA-I interval-based update strategy (V1 stores CLS features, V2 stores images). Evaluate FOA-I with intervals I={4,8,16,32,64} on ImageNet-C Gaussian noise (severity 5) alongside NoAdapt and TENT baselines. Verify I=4 outperforms TENT (BS=64) and smaller intervals yield better performance. Measure peak GPU memory for NoAdapt, TENT, CoTTA, FOA, FOA-8bit across batch sizes, and for FOA-I V1/V2. Verify: FOA uses less memory than gradient-based methods; FOA memory comparable to NoAdapt; FOA-I V1/V2 use less memory than FOA; quantization reduces memory; FOA on quantized model outperforms T3A and exceeds full-precision TENT by >2%. [hard]

**Success criteria:**

1. **[foa-t3a-]** (weight=1) FOA outperforms T3A significantly in both accuracy and ECE scores on both 8-bit and 6-bit models
2. **[foa-8bit]** (weight=1) FOA with 8-bit ViT achieves better accuracy than TENT with 32-bit ViT (with a > 2% improvement).
3. **[memory-m]** (weight=1) Memory usage is measured for different batch sizes for NoAdapt, TENT, CoTTA, FOA, and FOA (8-bit), measuring both runtime and peak GPU memory usage.
4. **[memory-8]** (weight=1) Memory usage for 8-bit models is calculated as 0.25x of the corresponding 32-bit model measurements, following Liu et al. (2021b).
5. **[3100d5c8]** (weight=1) Memory usage is measured for different interval lengths for FOA-I V1 (which stores features between updates) and FOA-I V2 (which stores images between updates).
6. **[foa-memo]** (weight=1) The memory usage of FOA is comparable or slightly higher than that of NoAdapt over all batch sizes.
7. **[gradient]** (weight=1) FOA uses significantly less memory than gradient-based methods for all batch sizes.
8. **[2ce903d7]** (weight=1) FOA-I V1 and FOA-I V2 use less memory than FOA.
9. **[57793664]** (weight=1) Quantizing models to 8 bits reduces memory usage.
10. **[715c6377]** (weight=1) Two storage mechanisms are implemented for interval-based updates: FOA-I V1 stores CLS token features between updates, while FOA-I V2 stores original input images between updates.
11. **[interval]** (weight=1) After every I samples, CMA optimization is performed using all stored samples as a batch, followed by deleting all I stored samples.
12. **[forward-]** (weight=1) Model inference is correctly performed all the samples via a forward pass.
13. **[interval]** (weight=1) FOA-I is trained and evaluated with intervals I = {4, 8, 16, 32, 64} as shown in Table 6.
14. **[noadapt-]** (weight=1) NoAdapt baseline performance is measured.
15. **[tent-bas]** (weight=1) TENT baseline with batch size 64 is measured.

### Subtask 10 of 10: Reproduce the robustness and generality experiments: in-distribution evaluation (Table 12), non-i.i.d. scenarios (Table 11), and alternative architectures (Table 10). For in-distribution: evaluate NoAdapt, TENT, CoTTA, SAR, FOA on clean ImageNet val; verify FOA retains near-NoAdapt accuracy (<2% degradation), outperforms other methods, achieves lower ECE than NoAdapt. For non-i.i.d.: create label-shift (class-ordered) and mixed-domain (interleaved corruptions) streams; evaluate TENT, SAR, FOA; verify FOA outperforms both under both settings with bounded degradation. For architectures: load ResNet-50 and VisionMamba; implement ResNet-50 prompts (7x7 Conv, uniform init, element-wise addition) and VisionMamba prompts (Np=3, concatenated); evaluate on ImageNet-C Gaussian noise (severity 5); verify FOA outperforms BN Adapt on ResNet-50 and FOA matches/exceeds TENT and SAR on VisionMamba. [hard]

**Success criteria:**

1. **[resnet50]** (weight=1) Code has been implemented such that a ResNet-50 model pre-trained on ImageNet-1K can be loaded into memory
2. **[visionma]** (weight=1) Code has been implemented such that a VisionMamba model pre-trained on ImageNet-1K can be loaded into memory
3. **[f6b90573]** (weight=1) The original ImageNet validation set is loaded without any corruptions or modifications.
4. **[3e77debc]** (weight=1) NoAdapt, TENT, CoTTA, SAR, and FOA are evaluated with consistent batch size 64 and using exactly the same validation samples.
5. **[noadapt-]** (weight=1) FOA maintains baseline NoAdapt accuracy with minimal degradation (< 2 %).
6. **[other-me]** (weight=1) FOA outperforms or is comparable to TENT, CoTTA, and SAR in terms of maintaining in-distribution accuracy.
7. **[ece-comp]** (weight=1) FOA achieves lower ECE on in-distribution data compared to NoAdapt
8. **[label-sh]** (weight=1) The ImageNet-C test data stream is arranged such that samples are encountered in class order, with instances from each class appearing consecutively.
9. **[label-sh]** (weight=1) Performance is evaluated on ImageNet-C (severity level 5) test samples arranged in class order.
10. **[mixed-do]** (weight=1) A single data stream is created that randomly mixes test samples from all 15 corruption types of ImageNet-C.
11. **[mixed-do]** (weight=1) Performance is evaluated on the mixed stream containing randomly interleaved samples from all corruption types.
12. **[method-c]** (weight=1) The three methods TENT, SAR, FOA are evaluated under the non-i.i.d. conditions (online imbalanced label shift and mixed domain shift).
13. **[performa]** (weight=1) The performance of all methods (TENT, SAR, FOA) shows some degradation under non-i.i.d. scenarios compared to i.i.d. scenarios, but FOA's degradation is bounded (ECE increase < 5%, accuracy decrease < [X]%).
14. **[relative]** (weight=1) FOA maintains better performance than TENT and SAR under both non-i.i.d. settings (online imbalanced label shifts and mixed domain shifts).
15. **[relative]** (weight=1) For each method, relative accuracy decline from NoAdapt is calculated by subtracting its accuracy from NoAdapt's [X]% baseline.

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/test-time-model-adaptation_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: test-time-model-adaptation

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
