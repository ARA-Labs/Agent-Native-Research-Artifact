# Full Paper Reproduction: self-composing-policies

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-composing-policies_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-composing-policies_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/self-composing-policies.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/self-composing-policies` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-composing-policies_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the CompoNet output attention head module as described in Section 4.2. This includes: (1) defining the prior-module output matrix Phi^{k;s} of size (k-1) x |A|; (2) computing h_s from the CNN encoder or raw state; (3) implementing the query via W_out^Q, the key via cosine positional embeddings E_out and W_out^K applied to (Phi + E_out), the value as Phi^{k;s}, and the scaled dot-product attention to produce output vector v; (4) verifying the only learnable parameters are W_out^Q and W_out^K. Unit-test that output shapes are correct and parameter count is independent of k. [easy]

**Success criteria:**

1. **[dbbb11b3]** (weight=1) A matrix $\Phi^{k;s}$ of size $(k-1) \times |A|$ is defined which stores the output vectors of all preceding $k - 1$ modules for the current state, where $k$ is the number of tasks seen so far (including the current one) and $A$ is the action space.
2. **[f0afda32]** (weight=1) Logic to compute $h_s \in \mathbb{R}^{d_{\text{enc}}}$ has been implemented, where $h_s$ is computed by the CNN encoder when encoding is needed (i.e., for the Arcade Learning Environment tasks) and $h_s = s$ when no encoder is needed (i.e., for the Meta-World tasks).
3. **[dda77699]** (weight=1) A parameter matrix $W_{out}^Q$ is defined with shape $d_{enc} \times d_{model}$ where $d_{enc}$ is the size of the encoded state vector and $d_{model}$ is the hidden size of the model.
4. **[7ce56b99]** (weight=1) The query vector is computed via $q = h_s W_{out}^Q$ where $h_s$ is the encoded state vector.
5. **[060b1284]** (weight=1) A parameter matrix $W_{out}^K$ is defined with shape $|A| \times d_{model}$ where $A$ is the action space and $d_{model}$ is the hidden size of the model.
6. **[cde1da9b]** (weight=1) A cosine positional embedding matrix $E_{out}$ of size $(k-1) \times |A|$ is defined.
7. **[0b8be057]** (weight=1) The key vector is computed via $(\Phi^{k;s} + E_{out}) W_{out}^Q$.
8. **[48b73614]** (weight=1) The logic to compute the value vector for the output attention head has been implemented, which is defined as $\Phi^{k;s}$ (the matrix of outputs from all previous modules).
9. **[76fa75da]** (weight=1) The output vector $v$ for the output attention head is computed via $\text { Attention }(\mathbf{q}, K, V)=\text{softmax}\left(\frac{q K^T}{\sqrt{d_{\text {model }}}}\right) V$.
10. **[bd7db785]** (weight=1) The only learnable parameters for the output attention head are $W_{out}^Q$ and $W_{out}^K$.

### Subtask 2 of 10: Implement the CompoNet input attention head and internal policy modules as described in Section 4.2. For the input attention head: (1) define matrix P as the row-wise concatenation of the output attention head result and Phi^{k;s}; (2) implement query via W_in^Q, key via cosine embeddings E_in and W_in^K, value via W_in^V, and scaled dot-product attention; (3) verify only W_in^Q, W_in^K, W_in^V are learnable. For the internal policy: (4) concatenate h_s with the input attention head output; (5) implement the MLP mapping d_enc + d_model to |A|; (6) verify only MLP parameters are learnable. For the final output: (7) sum the internal policy output with v from the output attention head; (8) implement normalization for continuous action spaces. [easy]

**Success criteria:**

1. **[d68e4314]** (weight=1) A matrix $P$ is defined as the row-wise concatenation of the output of the previous block (i.e., the output attention head) and $\Phi^{k;s}$ (the matrix of outputs from all previous modules).
2. **[cf3c7ec9]** (weight=1) A parameter matrix $W_{in}^Q$ is defined with shape $d_{enc} \times d_{model}$ where $d_{enc}$ is the size of the encoded state vector and $d_{model}$ is the hidden size of the model.
3. **[ef07a797]** (weight=1) The query vector is computed via $q = h_s W_{in}^Q$ where $h_s$ is the encoded state vector.
4. **[83e80a16]** (weight=1) A parameter matrix $W_{in}^K$ is defined with shape $|A| \times d_{model}$ where $A$ is the action space and $d_{model}$ is the hidden size of the model.
5. **[b40e5cba]** (weight=1) A cosine positional embedding matrix $E_{in}$ of the same size as $P$ is defined.
6. **[a75ab485]** (weight=1) The key vector is computed via $(P + E_{in}) W_{in}^K$.
7. **[eeb5aa73]** (weight=1) A parameter matrix $W_{in}^V$ is defined with shape $|A| \times d_{model}$ where $A$ is the action space and $d_{model}$ is the hidden size of the model.
8. **[467eb0c9]** (weight=1) The value vector is computed via $P W_{in}^V$.
9. **[2c041f24]** (weight=1) The output vector for the input attention head is computed via $\text { Attention }(\mathbf{q}, K, V)=\text{softmax}\left(\frac{q K^T}{\sqrt{d_{\text {model }}}}\right) V$.
10. **[a6657076]** (weight=1) The only learnable parameters for the input attention head are $W_{in}^Q$, $W_{in}^K$ and $W_{in}^V$.
11. **[d861366a]** (weight=1) The encoded state vector $h_s$ and the output of the input attention head module are concatenated column-wise, creating a vector of size $d_{enc} + d_{model}$.
12. **[0d54e498]** (weight=1) A multi-layer feed-forward block is implemented which maps a vector of length $d_{enc} + d_{model}$ to one of length $|A|$, where |A| is the dimensionality of the action space.
13. **[b2387837]** (weight=1) The only learnable parameters for the internal policy are those in the multi-layer feed-forward block.
14. **[5eb4989c]** (weight=1) An $|A|$-dimension vector is computed by adding the output of the internal policy module, a vector of size $|A|$, to the output from the output attention head, the vector previously denoted as $v$.
15. **[74545ee1]** (weight=1) Logic to normalize the summed vectors has been implemented for continuous action spaces.

### Subtask 3 of 10: Measure and compare the scalability of CompoNet vs ProgressiveNet in terms of parameter count and inference time, reproducing Figure 3. (1) Instantiate CompoNet and ProgressiveNet models for k in {1, 10, 50, 100, 150, 200, 250, 300} using the hyperparameters from the Figure 3 caption (d_enc=64, |A|=6, d_model=256, batch=8). (2) For each k, count total and trainable parameters for both architectures. (3) For each k, run inference for at least 1 minute and record average inference time. (4) Verify CompoNet parameter counts grow linearly (O(n)) while ProgressiveNet's grow quadratically. (5) Verify CompoNet inference time grows substantially slower than ProgressiveNet up to 300 tasks. [easy]

**Success criteria:**

1. **[82e6b6ac]** (weight=1) TODO: Logic to create a sequence of 300 tasks has been implemented using X (e.g. Meta-World or ALE or both).
2. **[b52da4ce]** (weight=1) CompoNet's inference time has been measured for an increasing number of tasks (from 1 up to 300, inclusive) whilst being trained on the Meta-World environments (TODO: Confirm this with the author). The measurements are conducted with the hyperparameters from Table E.1 and the caption of Figure 3 ([TODO: Confirm this with the author, remove once confirmed] giving precedence to the caption in the case of conflict), as described in Appendix C.2, with the results stored in a suitable data structure.
3. **[043beaa5]** (weight=1) ProgressiveNet's inference time has been measured for an increasing number of tasks (from 1 up to 300, inclusive) whilst being trained on the Meta-World environments (TODO: Confirm this with the author). The measurements are conducted with the hyperparameters from Table E.1 and the caption of Figure 3 ([TODO: Confirm this with the author, remove once confirmed] giving precedence to the caption in the case of conflict), as described in Appendix C.2, with the results stored in a suitable data structure.
4. **[56f8b909]** (weight=1) The recorded results show that the inference time (in seconds) of ProgressiveNet grows quadratically.
5. **[8d795b81]** (weight=1) The recorded results show that the inference time (in seconds) of CompoNet grows slower than ProgressiveNet, with the gap widening as the number of tasks increases.
6. **[8b74b662]** (weight=1) TODO: Logic to create a sequence of 300 tasks has been implemented using X (e.g. Meta-World or ALE or both).
7. **[1f60a8c9]** (weight=1) CompoNet's total and trainable parameter counts have been measured for an increasing number of tasks (from 1 up to 300, inclusive) whilst being trained on the Meta-World environments (TODO: Confirm this with the author). The measurements are conducted with the hyperparameters from Table E.1 and the caption of Figure 3 ([TODO: Confirm this with the author, remove once confirmed] giving precedence to the caption in the case of conflict), as described in Appendix C.2, with the results stored in a suitable data structure.
8. **[3a78e866]** (weight=1) ProgressiveNet's total and trainable parameter counts have been measured for an increasing number of tasks (from 1 up to 300, inclusive) whilst being trained on the Meta-World environments (TODO: Confirm this with the author). The measurements are conducted with the hyperparameters from Table E.1 and the caption of Figure 3 ([TODO: Confirm this with the author, remove once confirmed] giving precedence to the caption in the case of conflict), as described in Appendix C.2, with the results stored in a suitable data structure.
9. **[f0dafbe8]** (weight=1) The recorded results show that the total parameter count of CompoNet grows (roughly) linearly.
10. **[23a2aa0a]** (weight=1) The recorded results show that the trainable parameter count of CompoNet grows linearly.
11. **[318d3eee]** (weight=1) The recorded results show that the total parameter count of ProgressiveNet grows quadratically.
12. **[1df26f0a]** (weight=1) The recorded results show that the trainable parameter count of ProgressiveNet grows quadratically.

### Subtask 4 of 10: Implement the PPO training loop and configure all PPO hyperparameters from Table E.2 for the ALE continual learning experiments. (1) Adapt the PPO implementation from Huang et al. (2022) to use CompoNet as actor, compatible with both ALE environments. (2) Configure AdamW optimizer with betas (0.9, 0.999), max grad norm 0.5, gamma=0.99, d_model=512, lr=2.5e-4, vf_coef=0.5, GAE lambda=0.95, 8 parallel envs, batch=1024, 4 update epochs, clip=0.2, entropy_coef=0.01, lr annealing, clipped value loss, normalized advantages, 128 steps per rollout. (3) Implement two single-layer output heads for actor (logits of categorical distribution) and critic (value function). [easy]

**Success criteria:**

1. **[90f271f7]** (weight=1) The PPO implementation from Huang et al. (2022) has been adapted to use the CompoNet as an agent.
2. **[4f2a00e0]** (weight=1) The PPO implementation from Huang et al. (2022) has been further adapted to be compatible with both ALE environments used in the paper: `ALE/SpaceInvaders-v5` and `ALE/Freeway-v5`. TODO: Clarify the specific modifications made with the author.
3. **[04a582b9]** (weight=1) In the PPO implementation, the optimizer has been set to AdamW.
4. **[b5c20ebb]** (weight=1) In the PPO implementation, the $beta_1$ and $beta_2$ parameters of AdamW are set to 0.9 and 0.999 respectively.
5. **[24277bc2]** (weight=1) In the PPO implementation, the maximum gradient norm is set to 0.5.
6. **[b181f0b9]** (weight=1) In the PPO implementation, the discount rate ($\gamma$) has been set to 0.99.
7. **[61cf8fe3]** (weight=1) In the PPO implementation, the hidden dimension ($d_{model}) is set to 512.
8. **[9d838de5]** (weight=1) In the PPO implementation, the learning rate is set to $2.5 \cdot 10^{-4}$.
9. **[d8b7555f]** (weight=1) In the PPO implementation, the PPO value function coefficient is set to 0.5.
10. **[0193f558]** (weight=1) In the PPO implementation, the GAE ($\lambda$) is set to 0.95.
11. **[940b2a8a]** (weight=1) In the PPO implementation, the number of parallel environments is set to 8.
12. **[27f990db]** (weight=1) In the PPO implementation, the batch size is set to 1024.
13. **[eda94d3e]** (weight=1) In the PPO implementation, the number of update epochs is set to 4.
14. **[97903a43]** (weight=1) In the PPO implementation, the PPO clipping coefficient is set to 0.2.
15. **[b159646a]** (weight=1) In the PPO implementation, the PPO entropy coefficient is set to 0.01.

### Subtask 5 of 10: Implement the CNN encoder, SAC training loop, and evaluation metrics for the Meta-World continual learning setting. (1) Implement the 3-layer CNN encoder (32/64/64 channels, filters 8/4/3, dense 512) with weight inheritance across tasks, shared between actor and critic. (2) Adapt the SAC implementation from Huang et al. (2022) to use CompoNet as the actor, with the SAC-specific critic (2-layer MLP + mean/log-std heads), and configure all hyperparameters from Table E.1 (Adam, gamma=0.99, batch=128, buffer=1e6, tau=0.005, etc.). (3) Implement the average performance P(t), forward transfer FTr, and reference transfer RT metrics as described in Section 5.1. [medium]

**Success criteria:**

1. **[d92c7aa0]** (weight=1) The CNN has three convolutional layers with 32, 64 and 64 channels and filter sizes of 8, 4 and 3 respectively.
2. **[2eaeb892]** (weight=1) The CNN has a final dense layer with an output dimension of 512.
3. **[2c2ef685]** (weight=1) Logic to use a single CNN encoder per policy has been implemented, where the encoder for a new policy is initialized with the weights of the previous one, as described in Appendix E.2.
4. **[1f4b310c]** (weight=1) The output of the encoder is an input to both CompoNet (actor) as well as the value function (critic).
5. **[b57de4fc]** (weight=1) The SAC implementation from Huang et al. (2022) has been adapted to use the CompoNet as an agent.
6. **[9fe63a30]** (weight=1) The critic network has been implemented as a two-layer MLP followed by two separate output heads of a single layer corresponding to the mean and logarithm of the standard deviation of a normal distribution.
7. **[37d0398b]** (weight=1) The success rate for task $i$ at timestep $t$, $p_i(t)$, is available for all timesteps and is taken as an input, which corresponds to the success rate in task $i$ at time $t$.
8. **[0f95bb2e]** (weight=1) The average performance at timestep $t$ is computed as $P(t) = \frac{1}{N} \sum_{i=1}^N p_i(t)$
9. **[09cd146f]** (weight=1) The success rate for task $i$ at timestep $t$, $p_i(t)$, is available for all timesteps and is taken as an input, which corresponds to the success rate in task $i$ at time $t$.
10. **[3f61bfcd]** (weight=1) The baseline (i.e., training a randomly initialized NN for each task) success rate for each task, $p_i^b(t)$, is taken as an input, which corresponds to the success rate of the baseline method in task $i$ at time $t$.
11. **[07c21e51]** (weight=1) The area under the success curve ($\mathrm{AUC}_i=\frac{1}{\Delta} \int_{(i-1) \cdot \Delta}^{i \cdot \Delta} p_i(t) \mathrm{d} t$) for each task is computed, as described in Equation (2) of Section 5.1.
12. **[dbe45d3b]** (weight=1) The area under the baseline success curve ($\mathrm{AUC}_i^b=\frac{1}{\Delta} \int_0^{\Delta} p_i^b(t) \mathrm{d} t$) for each task is computed, as described in Equation (2) of Section 5.1.
13. **[a16438be]** (weight=1) The forward transfer metric $\mathrm{FTr}_i=\frac{\mathrm{AUC}_i-\mathrm{AUC}_i^b}{1-\mathrm{AUC}_i^b}$ has is computed, as described in Equation (2) of Section 5.1.
14. **[05714e8d]** (weight=1) The forward transfers, $\text{FTr}(j,i)$, obtained by training a model from scratch on the $j$-th task and fine-tuning it on the $i$-th task are taken as inputs for all $i$ and $j$ such that $1 \leq j < i \leq N$.
15. **[c76c362b]** (weight=1) Code for computing the reference forward transfer ($\mathrm{RT}=\frac{1}{N} \sum_{i=2}^N \max _{j<i} \mathrm{FTr}(j, i)$) has been implemented, as described in Equation (3) of Section 5.1.

### Subtask 6 of 10: Reproduce the Scenario (i) architectural validation experiment (Figures 4a-4d): efficient policy reuse with one informative prior. (1) Pre-train one policy module on SpaceInvaders task 5 (mode 4). (2) Define 4 non-informative random modules (uniform Dirichlet). (3) Train a new CompoNet module on task 5 with these 5 prior modules for 1M timesteps across 10 seeds. (4) Train a from-scratch baseline on the same task. (5) Record episodic returns, matching rates (Out=OutHead, Out=IntPol, OutHead=IntPol), input attention weights per module, and output attention weights per module at least every 10k timesteps. (6) Verify CompoNet sharply surpasses baseline within 200k timesteps. (7) Verify output attention head concentrates on the informative module (approaching 1.0 within 10k timesteps). (8) Verify input attention head assigns ~[X] to the output head row and ~[X] to the informative module while non-informative modules drop to ~0. [medium]

**Success criteria:**

1. **[b777444f]** (weight=1) A single informative policy (i.e., one that provides relevant knowledge for solving a future task) has been pre-trained on the 5th task (i.e., the 4th playing mode) of SpaceInvaders using the SAC algorithm and the hyperparameters in Table E.1 (TODO: Confirm with author), with its weights saved for later reuse.
2. **[feec8fca]** (weight=1) Four non-informative policies have been defined and implemented to act as random policies i.e., they each sample an action from a uniform Dirichlet distribution.
3. **[5f0ec7d2]** (weight=1) A new CompoNet module has been instantiated for the 5th task of SpaceInvaders, referencing the four non-informative modules and the single informative module as its (frozen) predecessors, ensuring the parameters of all previous modules are frozen.
4. **[4dca3b7d]** (weight=1) A total of 10 random seeds have been set before each training run.
5. **[75042767]** (weight=1) The newly added CompoNet module has been trained for 1M timesteps on the 5th task of SpaceInvaders using the SAC algorithm, while keeping the parameters of all previous modules frozen.
6. **[4f725a8e]** (weight=1) The baseline method was trained on the 5th task (i.e., the 4th playing mode) of SpaceInvaders for 1M timesteps per seed using the SAC algorithm and the hyperparameters in Table E.1 (TODO: Confirm with the author, remove once confirmed).
7. **[ca4ae1dd]** (weight=1) The episodic returns have been computed at regular intervals (at least every 10k timesteps) and saved during training of the baseline method for each seed.
8. **[d1993d1e]** (weight=1) The episodic returns have been computed at regular intervals (at least every 10k timesteps) and saved during training of CompoNet for each seed.
9. **[c0916ef4]** (weight=1) The saved episodic returns for CompoNet show that the mean episodic returns sharply increases within the first 200k timesteps, then plateaus at around 600.
10. **[d7e80724]** (weight=1) The saved episodic returns for the baseline method show that the mean episodic returns steadily increases over time, eventually reaching an episodic return of around 400 by the 1M timestep mark.
11. **[4a93d5d7]** (weight=1) The mean matching rate of the final output and the output head shows that, in the initial timesteps, the final output of the model matches with the result of the output attention head, and the internal policy is barely used.
12. **[6c83fb26]** (weight=1) The mean matching rate of the final output and the output head shows that, after several timesteps, the internal policy learns to imitate the result of the output attention head, which is mostly used as the final output of the model.
13. **[1037dc3f]** (weight=1) The mean output head's attention scores for the informative policy sharply increases to 1.0 within the first 10k timesteps, plateaus at 1.0 and stays at 1.0 thereafter.
14. **[bf94fcd9]** (weight=1) The mean of the output head's attention scores for all four non-informative policies drops to around 0.0 within the first 10k timesteps and stays at around 0.0 thereafter.

### Subtask 7 of 10: Reproduce the Scenario (iii) architectural validation experiment (Figures 4e-4h): interference-free learning from scratch with all non-informative priors. (1) Define 5 non-informative random modules (uniform Dirichlet). (2) Train a new CompoNet module on SpaceInvaders task 6 (mode 5) with these 5 prior modules for 1M timesteps across 10 seeds. (3) Train a from-scratch baseline on the same task. (4) Record episodic returns, matching rates, input attention weights, and output attention weights at least every 10k timesteps. (5) Verify CompoNet matches baseline performance (no degradation from uninformative priors). (6) Verify the internal policy fully determines the final output (matching rates show Out=IntPol dominates). (7) Verify both attention heads distribute attention uniformly (~[X] per input for input head, ~[X] per module for output head, no single module >0.125 above the mean). [medium]

**Success criteria:**

1. **[a16cd6bb]** (weight=1) Five non-informative policies have been defined and implemented to act as random policies i.e., they each sample an action from a uniform Dirichlet distribution.
2. **[a377e3c6]** (weight=1) A new CompoNet module has been instantiated for the 6th task (i.e., the 5th playing mode) of SpaceInvaders, referencing the 5 non-informative policies as its predecessors.
3. **[a52a28e5]** (weight=1) A total of 10 random seeds have been set before each training run.
4. **[57fe4f9d]** (weight=1) The newly added CompoNet module has been trained for 1M timesteps on the 6th task (i.e., the 5th playing mode) of SpaceInvaders using the SAC algorithm.
5. **[315a31da]** (weight=1) The baseline method was trained on the 6th task (i.e., the 5th playing mode) of SpaceInvaders for 1M timesteps per seed using the SAC algorithm and the hyperparameters in Table E.1 (TODO: Confirm with the author, remove once confirmed).
6. **[231696e0]** (weight=1) The episodic returns have been computed at regular intervals (at least every 10k timesteps) and saved during training of the baseline method for each seed.
7. **[17f0e736]** (weight=1) The episodic returns have been computed at regular intervals (at least every 10k timesteps) and saved during training of CompoNet for each seed.
8. **[19014129]** (weight=1) The saved episodic returns for CompoNet show that the mean episodic returns increases steadily with time, exceeding 400 by 1M timesteps.
9. **[b64840ed]** (weight=1) The saved episodic returns for the baseline method show that the mean episodic returns increases steadily with time, falling short of the mean episodic returns of CompoNet at the 1M timestep mark.
10. **[5adbab63]** (weight=1) The mean matching rate of the final output and the output attention head sharply increases to exceed 0.8 (out of a maximum 1.0) within 10k timesteps then plateaus between 0.8 and 1.0.
11. **[2c237954]** (weight=1) The mean matching rates show that the final output of the model is completely determined by the internal policy after a few training steps, effectively overwriting the result of the output attention head.
12. **[652b7dd2]** (weight=1) The mean of the input head's attention scores for all 5 non-informative policies is stable at 0.18 plus or minus 0.125 across all timesteps.
13. **[b91fef48]** (weight=1) The mean of the output head's attention scores for all 5 non-informative policies is stable at 0.2 plus or minus 0.125 across all timesteps.
14. **[9e0900d2]** (weight=1) No one head has significantly (i.e. > 0.125) higher mean attention scores at any timestep.

### Subtask 8 of 10: Implement all five baseline methods (Baseline, FT-1, FT-N, ProgressiveNet, PackNet) for both Meta-World and ALE environments. (1) Implement the Baseline method (randomly initialized MLP per task) for Meta-World (39-dim state) and ALE (512-dim state). (2) Implement FT-1 (single continuously fine-tuned NN across all tasks) for both settings. (3) Implement FT-N (re-initialize output heads per task, save model params after each task) for both settings. (4) Implement ProgressiveNet (new column per task, lateral connections between columns, freeze prior column parameters, save parameters when task changes). (5) Implement PackNet (prune trained network per task, retrain 200K steps, freeze selected parameters, allocate parameter budget). [hard]

**Success criteria:**

1. **[97ddc4c5]** (weight=1) The baseline method has been implemented for the Meta-World environments, which is a randomly initialized MLP that maps a 39-dimensional state vector to two separate heads: one outputting the mean of a Gaussian distribution for each of the 4 actions and another outputting the log standard deviations.
2. **[0345c389]** (weight=1) The baseline method has been implemented for the ALE environments, which is a randomly intialized MLP mapping a 512-dimensional state vector to a 6-dimensional action space. The network outputs logits for a categorical distribution over these 6 actions.
3. **[96dbde05]** (weight=1) The baseline method has been implemented such that a randomly initialized neural network is trained from scratch for each task.
4. **[63030bd7]** (weight=1) The FT-1 method has been implemented for the Meta-World environments, which is a randomly initialized MLP that maps a 39-dimensional state vector to two separate heads: one outputting the mean of a Gaussian distribution for each of the 4 actions and another outputting the log standard deviations.
5. **[73ae5d74]** (weight=1) The FT-1 method has been implemented for the ALE environments, which is a randomly intialized MLP mapping a 512-dimensional state vector to a 6-dimensional action space. The network outputs logits for a categorical distribution over these 6 actions.
6. **[798a234f]** (weight=1) The FT-1 method has been implemented so that it continuously fine-tune a single NN across all tasks.
7. **[de8d83b9]** (weight=1) The FT-N method has been implemented for the Meta-World environments, which is a randomly initialized MLP that maps a 39-dimensional state vector to two separate heads: one outputting the mean of a Gaussian distribution for each of the 4 actions and another outputting the log standard deviations.
8. **[4fd52a4e]** (weight=1) The FT-N method has been implemented for the ALE environments, which is a randomly intialized MLP mapping a 512-dimensional state vector to a 6-dimensional action space. The network outputs logits for a categorical distribution over these 6 actions.
9. **[1b7ece23]** (weight=1) The logic to save model parameters after training on each task has been implemented.
10. **[bce385fe]** (weight=1) The logic to re-initialize the output heads at the beginning of each task has been implemented.
11. **[b7dccfee]** (weight=1) Logic to instantiate a new network (with random initial parameters) every time the task changes has been implemented.
12. **[b363705b]** (weight=1) Logic to add lateral connections (TODO: be more specific about what a lateral connection is after asking author) between the current network and the ones learned in previous tasks when a new network is added has been implemented.
13. **[9ff4ad97]** (weight=1) Logic to freeze the parameters of the neural networks trained on previous tasks has been implemented.
14. **[1cbbd1d1]** (weight=1) Logic to prune the trained network after each task has been implemented, selecting the weights that are most relevant for the current task, has been implemented.
15. **[60c403cd]** (weight=1) Logic to retrain the pruned network for the current task has been implemented has been implemented.

### Subtask 9 of 10: Train and evaluate all six methods on the Meta-World 20-task sequence (Table 1, Meta-World columns). Using SAC with Table E.1 hyperparameters, train Baseline, FT-1, FT-N, ProgressiveNet, PackNet, and CompoNet for 10 seeds x 1M timesteps per task on the 20-task Meta-World sequence (10 environments repeated twice). Record success rates per task per seed. Compute average performance P(T) and forward transfer FTr for each method per seed, then report mean and std across seeds. Verify CompoNet achieves the highest or tied-highest average performance and forward transfer on Meta-World, and is the only method with non-negative forward transfer. [hard]

**Success criteria:**

1. **[dabaeb40]** (weight=1) A total of 10 random seeds have been set before each training run.
2. **[066903cf]** (weight=1) A total of 1M timesteps have been used per task.
3. **[8036351f]** (weight=1) The baseline method has been trained on the Meta-World sequence of tasks for each seed.
4. **[40f3d0f3]** (weight=1) The success rates for each task and seed has been recorded.
5. **[d5f9b44a]** (weight=1) The CompoNet method has been trained on the Meta-World sequence of tasks for each seed.
6. **[90c21094]** (weight=1) The success rates for each task and seed has been recorded.
7. **[15067927]** (weight=1) The average performance metric has been computed for each method and seed (i.e., 50 metrics in total).
8. **[a8a243b1]** (weight=1) The forward transfer metric has been computed for each method and seed (i.e., 50 metrics in total).
9. **[ddd24b5c]** (weight=1) The mean and standard deviation of the average performance and forward transfer metrics have been computed for every method and every task sequence across all 10 seeds using the saved results.
10. **[319edc0d]** (weight=1) The mean average performance metrics show that CompoNet preforms at least as well as all other methods (higher is better) across all three task sequences.
11. **[0d79cc8d]** (weight=1) The mean forward transfer metrics show that CompoNet preforms at least as well as all other methods (higher is better) across all three task sequences.
12. **[6ddede73]** (weight=1) The `hammer-v2` environment can be built using `gym.make`.
13. **[915fdd73]** (weight=1) The Metaworld module (https://github.com/Farama-Foundation/Metaworld) is used to define the environments.
14. **[d1f984f0]** (weight=1) The logic to generate a sequence of 20 tasks (i.e., a sequence of all 10 Meta-World environments repeated repeated twice) has been implemented, as described in Section 5.2.
15. **[09240921]** (weight=1) All 10 tasks in the sequence run for 1M timesteps each for a total of 20M timesteps, as described in Section 5.2.

### Subtask 10 of 10: Train and evaluate all six methods on the SpaceInvaders 10-task sequence (Table 1, SpaceInvaders columns). Using PPO with Table E.2 hyperparameters, train Baseline, FT-1, FT-N, ProgressiveNet, PackNet, and CompoNet for 10 seeds x 1M timesteps per task on the 10 playing modes of ALE/SpaceInvaders-v5. Record success rates per task per seed using the thresholds from Table D.1a. Compute P(T) and FTr for each method per seed, then report mean and std. Set up the ALE SpaceInvaders environment with Gymnasium, configure the 17-task ALE sequence, and implement the PPO critic with single-layer output heads and critic reset at task boundaries. Verify CompoNet achieves the highest forward transfer and highest or tied-highest performance on SpaceInvaders. [hard]

**Success criteria:**

1. **[4cae0a3a]** (weight=1) A total of 10 random seeds have been set before each training run.
2. **[1504ba8d]** (weight=1) A total of 1M timesteps have been used per task.
3. **[a1e3bc32]** (weight=1) The baseline method has been trained on the SpaceInvaders sequence of tasks for each seed.
4. **[a7c5323e]** (weight=1) The success rates for each task and seed has been recorded.
5. **[17775db7]** (weight=1) The CompoNet method has been trained on the SpaceInvaders sequence of tasks for each seed.
6. **[8353a180]** (weight=1) The success rates for each task and seed has been recorded.
7. **[65452b97]** (weight=1) The `ALE/SpaceInvaders-v5` environment can be built using `gym.make`.
8. **[db4ec248]** (weight=1) The Gymnasium module (https://github.com/Farama-Foundation/Gymnasium) is used to define the environments.
9. **[f7c172f9]** (weight=1) The logic to generate a sequence of 17 tasks (i.e., a sequence of all 10 playing modes of `ALE/SpaceInvaders-v5` followed by all 7 playing modes of `ALE/Freeway-v5`) has been implemented, as described in Section 5.2.
10. **[e4ba16c0]** (weight=1) All 17 tasks in the sequence run for 1M timesteps each for a total of 17M timesteps, as described in Section 5.2.
11. **[2bd5f28c]** (weight=1) A total of 10 random seeds have been set before each training run.
12. **[93d94ac7]** (weight=1) Two single-layer output heads are used to generate the logits of the categorical distribution over the action space (actor) and to compute the value function (critic).
13. **[f94431f2]** (weight=1) Logic to reset the critic network at the beginning of each task has been implemented.

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/self-composing-policies_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: self-composing-policies

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
