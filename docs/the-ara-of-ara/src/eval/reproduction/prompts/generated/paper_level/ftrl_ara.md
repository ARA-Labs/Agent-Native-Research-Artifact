# Full Paper Reproduction: ftrl

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/ftrl_ara_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/ftrl_ara_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the paper's **structured research artifact (ARA)**. You have NO access to the original paper PDF or its companion GitHub repository.

**ARA artifact location**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/artifacts/ftrl`

**How to navigate it:**

| Path | What it contains |
|------|-----------------|
| `PAPER.md` | Overview and index — **read this first** |
| `logic/claims.md` | Paper's claims, hypotheses, falsification criteria |
| `logic/experiments.md` | Experimental setups, datasets, hyperparameters, evaluation protocols |
| `logic/concepts.md` | Key technical concepts and definitions |
| `logic/solution/` | Algorithm details, architecture specifications, mathematical formulations |
| `src/` | Implementation configs, environment setup, dependency lists, execution instructions |
| `evidence/` | Reported results, figure data, table data |

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/ftrl_ara_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the three knowledge retention methods for RoboticSequence fine-tuning: EWC, BC, and Episodic Memory (EM). For EWC, compute the diagonal Fisher matrix analytically using 2560 replay buffer samples with clipping at 1e-5, implement the Fisher-weighted L2 penalty with actor reg coef 100 and critic reg coef 0. For BC, implement the expert data buffer construction at end of each task, KL-divergence actor loss and L2 critic loss with actor reg coef 1 and critic reg coef 0. For EM, set up the 100k replay buffer pre-loaded with 10k pre-trained transitions. Ensure KR methods are not applied to critic parameters. Implement the evaluation metrics: overall success rate, log-likelihood tracking every 50k steps on push-wall expert trajectories, and 2D PCA projections of log-likelihoods. [easy]

**Success criteria:**

1. **[8a8f1d29]** (weight=1) In the RoboticSequence environment, during fine-tuning, the SAC replay buffer its initialized with 10,000 state-action-reward tuples from the pre-trained stages using the pre-trained policy (i.e. the policy trained to convergence on the last two stages)
2. **[ccc41e40]** (weight=1) For the RoboticSequence environment, the diagonal of the Fisher information matrix $\mathcal{I}$ can be computed as $\mathcal{I}_{kk} = \left( \frac{\delta\mu}{\delta\theta_k} \cdot \frac{1}{\sigma}\right)^2 + 2 \left( \frac{\delta\sigma}{\delta\theta_k} \cdot \frac{1}{\sigma}\right)^2$, where $\mu : \mathbb{R} \mapsto \mathbb{R}$, and $\sigma : \mathbb{R} \mapsto \mathbb{R}$
3. **[70f0fef8]** (weight=1) For the RoboticSequence environment, for the elastic weight consolidation (EWC) implementation, the diagonal of the Fisher matrix is correctly computed as $F_k = \mathbb{E}_{x \sim \mathcal{D}} \mathbb{E}_{y \sim p_{\theta}(\cdot | x)} \left( \nabla_{\theta_k} \log p_{\theta_k} (y | x) \right)^2$, where the outer expectation is approximated with a sample of 2560 examples from the replay buffer $\mathcal{D}$, and the inner expectation is computed following the previous equation
4. **[bea5ee41]** (weight=1) For the RoboticSequence environment, for the elastic weight consolidation (EWC) implementation, the diagonal of the Fisher matrix is clipped so the minimal value is $10^{-5}$
5. **[4d4773c7]** (weight=1) For the RoboticSequence environment the Elastic Weight Consolidation (EWC) knowledge retention method is implemented; the auxiliary loss is implemented as $\mathcal{L}_{\text{aux}} (\theta) = \sum_i F^i(\theta_\star^i-\theta^i)^2$, where $\theta$ is the weights of the current model, $\theta_\star$ is the weights of the pre-trained model, and $F$ is the diagonal of the Fisher matrix
6. **[6e7fab7d]** (weight=1) For the RoboticSequence environment, for the elastic weight consolidation (EWC) implementation, the actor regularization coefficient is set to 100
7. **[5d88c498]** (weight=1) For the RoboticSequence environment, for the elastic weight consolidation (EWC) implementation, the critic regularization coefficient is set to 0
8. **[d77a7704]** (weight=1) For the RoboticSequence environment, for the behavioural cloning (BC) implementation, at the end of each task during training, a subset from the SAC buffer is randomly sampled, it is labeled using the outputs of the current (trained) networks and added to a separate buffer as "expert" data
9. **[1f96ce79]** (weight=1) For the RoboticSequence environment, for the behavioural cloning (BC) implementation, in all tasks apart from the first and second, auxiliary loss is added to the SAC's objective to imitate the expert data; for the actor, KL divergence is used, and for the critics, the L2 loss is used (which can be derived as KL divergence between mean-parameterized Gaussian distributions).
10. **[13ae6f4b]** (weight=1) For the RoboticSequence environment, for the behavioural cloning (BC) implementation, the actor regularization coefficient is set to 1
11. **[df3e311a]** (weight=1) For the RoboticSequence environment, for the behavioural cloning (BC) implementation, the critic regularization coefficient is set to 0
12. **[d7690cb7]** (weight=1) For the RoboticSequence environment, for the episodic memory (EM) implementation, the size of the replay buffer is 100k
13. **[c9ac831b]** (weight=1) For the RoboticSequence environment, for the episodic memory (EM) implementation, when fine-tuning models transitions are sampled from both online trajectories and trajectories stored in the repay buffer
14. **[395a870b]** (weight=1) For the RoboticSequence environment, the knowledge retention methods are not applied to the parameters of the critic
15. **[47c00516]** (weight=1) When a model has been trained for N steps on RoboticSequence, the success rate is computed as the average success rate over all steps in the trajectory

### Subtask 2 of 10: Train all five RoboticSequence conditions (from scratch, vanilla FT, FT+EWC, FT+BC, FT+EM) with 20 seeds each and verify the Section 4 overall performance results (Figure 4). Pre-train SAC on the last two stages (peg-unplug-side, push-wall) until 100% success. Run all conditions and verify that: (1) BC and EM achieve similar overall success rate ([X]%); (2) BC and EM achieve higher success than all other methods; (3) EWC outperforms vanilla FT; (4) vanilla FT matches from-scratch performance; (5) BC achieves ~[X] success at 1e6 steps and plateaus. [easy]

**Success criteria:**

1. **[795dc510]** (weight=1) For the RobiticSequence environment, the "pre-trained" SAC model is obtained by initializing with random weights and pre-training from scratch on the last two stages in multi-task setting (peg-unplug-side and push-wall) until convergence (i.e. 100% success rate)
2. **[68b4ae69]** (weight=1) For the RobiticSequence environment, the "from scratch" SAC model is obtained by initializing with random weights and pre-training from scratch on the RoboticSequence environment. The model is trained 20 separate times with 20 unique seeds
3. **[077c51ef]** (weight=1) The pre-trained (from scratch) model is fine-tuned on the RoboticSequence environment. The model is trained 20 separate times with 20 unique seeds
4. **[9037e949]** (weight=1) The pre-trained (from scratch) model is fine-tuned with behavioral cloning (BC) on the RoboticSequence environment. The model is trained 20 separate times with 20 unique seeds
5. **[a77dae72]** (weight=1) The pre-trained (from scratch) model is fine-tuned with elastic weight consolidation (EWC) on the RoboticSequence environment. The model is trained 20 separate times with 20 unique seeds
6. **[6dd3c5b1]** (weight=1) The pre-trained (from scratch) model is fine-tuned with episodic memory (EM) on the RoboticSequence environment. The model is trained 20 separate times with 20 unique seeds
7. **[290e0d26]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 4 show that fine-tuning coupled with behavioural cloning (BC) achieves a success rate similar to fine-tuning coupled with episodic memory (EM) by the end of training
8. **[3413b8ea]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 4 show that both fine-tuning coupled with behavioural cloning (BC) and fine-tuning coupled with episodic memory (EM) achieve a success rate higher than all other methods by the end of training
9. **[b483620e]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 4 show that fine-tuning coupled with elastic weight consolidation (EWC) achieves a success rate higher than vanilla fine-tuning by the end of training
10. **[e28e4430]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 4 show that vanilla fine-tuning achieves a success rate similar to pre-training from scratch by the end of training
11. **[2bcf4f7f]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 4 show that fine-tuning coupled with behavioural cloning (BC) achieves a success rate of around 0.8 at 1e6 steps, then plateaus at 0.8 success rate until the end of training

### Subtask 3 of 10: Evaluate per-stage forgetting dynamics and representation analysis for RoboticSequence (Section 5, Figures 7-8). Using all five conditions with 20 seeds each, track per-stage success rates throughout training and compute log-likelihood/PCA analysis. Verify that: (1) all methods reach >90% hammer success within 1e6 steps; (2) all methods reach >80% push success, FT methods learn faster; (3) BC never drops below 90% on peg-unplug-side or push-wall; (4) EM initially drops below 20% on peg-unplug-side but recovers to >90%; (5) EWC drops below 65% on peg-unplug-side but recovers; (6) vanilla FT push-wall success drops to near 0 after 100k steps then recovers above 0.8 by 4M steps; (7) PCA projections confirm the re-learned solution is qualitatively different from the pre-trained one. [easy]

**Success criteria:**

1. **[4778e195]** (weight=1) When training models on RoboticSequence, the log-likelihoods under the fine-tuned policy of trajectories collected using $\pi_\star$ on "push-wall" are computed every 50 thousand training steps, where $\pi_\star$ is the pre-trained policy (trained to convergence on the final two tasks)
2. **[c455e8ed]** (weight=1) When training models on RoboticSequence, the 2D PCA projections of the log-likelihoods under the fine-tuned policy of trajectories are collected using $\pi_\star$ on "push-wall" are computed, where $\pi_\star$ is the pre-trained policy (trained to convergence on the final two tasks)
3. **[a8b6b1ec]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that all training methods (apart from the pre-trained frozen baseline) achieve a success rate around or above 90% for the hammer sub-task within 1e6 steps, and maintain a success rate around or above 90% for the hammer sub-task for the remaining course of training
4. **[4870459d]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that all training methods (apart from the pre-trained frozen baseline) achieve a success rate around or above 80% for the push sub-task by the end of training
5. **[9586bf60]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that all training methods (apart from the pre-trained frozen baseline and pre-training from scratch) learn faster than the pre-training from scratch method for the push sub-task
6. **[463556ff]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with behavioural cloning (BC) doesn't have a success rate under 90% for the peg-unplug-side sub-task over the course of training
7. **[063cde22]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with episodic memory (EM) achieves a success rate <20% within 1e6 steps of training for the peg-unplug-side sub-task, then the success rate increases to around or above 90% by the end of training
8. **[5f3570bd]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with elastic weight consolidation (EWC) achieves a success rate <65% within 1e6 steps of training for the peg-unplug-side sub-task, then the success rate increases to around or above 90% by the end of training
9. **[98f86761]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with behavioural cloning (BC) doesn't have a success rate under 90% for the push-wall sub-task over the course of training
10. **[c2d77e0d]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with episodic memory (EM) achieves a success rate <10% within 1e6 steps of training for the push-wall sub-task, then the success rate increases to around or above 85% by the end of training
11. **[720064ae]** (weight=1) The recorded metrics for the RoboticSequence experiments in Section 5 show that the fine-tuning coupled with elastic weight consolidation (EWC) achieves a success rate <50% within 1e6 steps of training for the push-wall sub-task, then the success rate increases to around or above 60% by the end of training
12. **[18e0442a]** (weight=1) The recorded metrics show that the success rate on the "push-wall" task of the fine-tuned policy on RoboticSequence rapidly drops at the start of training, going to a success rate of almost 0 after 100k steps
13. **[cfafddf9]** (weight=1) The recorded metrics show that the success rate on the "push-wall" task of the fine-tuned policy on RoboticSequence recovers after around 4M steps; by 4M steps the success rate is above >0.8
14. **[f7eb45e0]** (weight=1) The computed PCA projections of the fine-tuned policy on RoboticSequence demonstrates that the model forgets the initial solution and is unable to recover it

### Subtask 4 of 10: Implement the NetHack environment, LSTM model architecture, data pipeline, and APPO training infrastructure. Set up the NetHack environment from NLE, implement the 30M LSTM architecture (ReLU, hidden dim 1738), acquire the Tuyls et al. (2023) pre-trained checkpoint, construct the NLD-AA dataset (8000 Human Monk games), and configure APPO training with all hyperparameters from Table 1 (ADAM optimizer with specified betas, lr 0.0001, weight decay 0.0001, batch size 128, gradient clipping 4, discount 0.999999, rollout size 32, clip 0.1, baseline cost 1.0, entropy cost 0.001, reward clipping +-10). Implement the critic head pre-training for 500M steps and encoder freezing during fine-tuning. Also implement the evaluation protocol (average return, rollout termination conditions, max dungeon level tracking). [medium]

**Success criteria:**

1. **[e38df225]** (weight=1) The NetHack environment has been imported from https://github.com/heiner/nle
2. **[9f015c64]** (weight=1) For NetHack, the 30M LSTM uses ReLU activation functions
3. **[3ec91367]** (weight=1) For NetHack, the 30M LSTM uses a hidden dimensionality of 1738
4. **[acfc8769]** (weight=1) The 30M pre-trained LSTM trained by "Scaling Laws for Imitation Learning in Single-Agent Games" (Tuyls et al. (2023)) is available. The weights are downloaded from https://drive.google.com/uc?id=1tWxA92qkat7Uee8SKMNsj-BV1K9ENExl
5. **[47b7bf81]** (weight=2) The NLD-AA dataset is constructed by following the instructions from https://github.com/dungeonsdatasubmission/dungeonsdata-neurips2022
6. **[556adc51]** (weight=1) 8000 games of Human Monk are randomly selected from the NLD-AA dataset, to make up the dataset used for training models on NetHack
7. **[4fa5d4b0]** (weight=1) APPO is used when training all models on the NetHack environment, using the implementation from https://github.com/alex-petrenko/sample-factory/
8. **[aa4932c4]** (weight=1) In NetHack, when fine-tuning any model (not when pre-training models from scratch), the model is first pre-trained for 500M environment steps where the entire model is frozen aside from the critic head
9. **[3ccae3d0]** (weight=1) When fine-tuning models in the NetHack environment, all encoders are frozen during the course of the training
10. **[e31bc54b]** (weight=1) For the experiments in Section 4 related to NetHack, the average return for a method that has been trained for N steps is computed as the average return over all steps in the trajectory
11. **[d63bf606]** (weight=1) When evaluating an agent on NetHack, the agent is rolled out until 1) it dies, 2) 150 steps are taken without progress being made, or 3) 100k steps are taken
12. **[506f55fb]** (weight=1) For the experiments in Section 4 related to NetHack, the maximum dungeon level achieved over the course of training is recorded

### Subtask 5 of 10: Implement the NetHack per-level evaluation infrastructure and verify Section 5 forgetting results (Figures 3b-c). Set up AutoAscend to generate 200 game saves from Level 4 and 200 from the first Sokoban level. Implement per-level evaluation: load saved games, run the trained agent, measure incremental score every 25M steps. Verify that: (1) FT+KS and FT+BC achieve higher Level 4 return than the frozen baseline; (2) EWC matches baseline on Level 4; (3) vanilla FT and from-scratch score lower on Level 4; (4) FT+BC matches baseline on Sokoban; (5) FT+KS and FT+EWC score below baseline on Sokoban; (6) vanilla FT and from-scratch achieve near-zero Sokoban scores (~[X]); (7) FT+KS visits deeper dungeon levels than pre-trained, but AutoAscend visits deeper still. [medium]

**Success criteria:**

1. **[5b808a19]** (weight=1) The NetHack environment has been modified to support saving and loading the game
2. **[03f1e111]** (weight=1) AutoAscend has been implemented, using the implementation from https://github.com/cdmatters/autoascend/tree/jt-nld
3. **[832dc72d]** (weight=1) The AutoAscend agent is executed to play the game and save the state when it reaches Level 4 of NetHack. 200 game saves satisfying such criteria are generated
4. **[c039593c]** (weight=1) The AutoAscend agent is executed to play NetHack and save the state when it reaches the first level of Sokoban. 200 game saves satisfying such criteria are generated
5. **[b3967331]** (weight=1) For the experiments in Section 5 related to NetHack, to compute the Level 4 evaluation, the model is evaluated on each of the 200 saves generated by AutoAscend by loading each game (running the agent where the AutoAscend agent finished) and computing the score the model achieved on top of the AutoAscend agent's score. The average score across the 200 game saves is computed as the average return
6. **[14de6420]** (weight=1) For the experiments in Section 5 related to NetHack, the average return from Level 4 is computed every 25 million training steps
7. **[b1075dca]** (weight=1) For the experiments in Section 5 related to NetHack, to compute the Sokoban score (number of filled pits), the model is evaluated on each of the 200 saves by loading each game (running the agent where the AutoAscend agent finished) and computing the score the model achieved on top of the AutoAscend agent's score (number of filled pits). The average score across the 200 game saves is computed as the Sokoban score
8. **[c1894983]** (weight=1) For the experiments in Section 5 related to NetHack, the average Sokoban score (number of filled pits) is computed every 25 million training steps
9. **[ee8c8b60]** (weight=1) The recorded metrics show that fine-tuning with kickstarting (KS) is significantly more likely to visit later dungeon levels than the pre-trained policy
10. **[f552f42a]** (weight=1) The recorded metrics show that AutoAscend is significantly more likely to visit later dungeon levels than fine-tuning with kickstarting (KS)
11. **[46d4aab1]** (weight=1) The recorded metrics for the NetHack experiments in Section 5 show that both fine-tuning coupled with kickstarting (KS) and fine-tuning coupled with behavioral cloning (BC) achieve a higher performance from Level 4 (average return from level 4) than the frozen pre-trained baseline (Tuyls et al., 2023) by the end of training
12. **[3391c6e9]** (weight=1) The recorded metrics for the NetHack experiments in Section 5 show that fine-tuning coupled with elastic weight consolidation (EWC) achieves a higher performance from Level 4 (average return from level 4) roughly equivalent to the frozen pre-trained baseline (Tuyls et al., 2023) by the end of training
13. **[60d7694f]** (weight=1) The recorded metrics for the NetHack experiments in Section 5 show that both vanilla fine-tuning and pre-training from scratch achieve a lower performance on Level 4 (average return from level 4) than the frozen pre-trained baseline (Tuyls et al., 2023) by the end of training
14. **[7a1c8f49]** (weight=1) The recorded metrics for the NetHack experiments in Section 5 show that fine-tuning coupled with behavioral cloning (BC) achieves an average Sokoban score roughly equivalent to frozen pre-trained baseline (Tuyls et al., 2023) by the end of training
15. **[6b8bbb64]** (weight=1) The recorded metrics for the NetHack experiments in Section 5 show that both vanilla fine-tuning and pre-training from scratch achieve an average Sokoban score roughly equivalent to 0.1 (+-0.1) by the end of training

### Subtask 6 of 10: Implement the RoboticSequence (Meta-World) environment and SAC training infrastructure. Define RoboticSequence as a 4-stage sequential task (hammer, push, peg-unplug-side, push-wall) with random starting positions and goal conditions, one-hot stage ID encoding, normalized timestep, max 200 steps, and reward augmentation on success (beta=1.5). Implement the 4-layer MLP (256 neurons, Leaky-ReLU, layer norm after first layer) for both policy and Q-function. Set up SAC with auto-tuned entropy, stage-conditioned output heads, 100k replay buffer, correct terminal signal handling, per-stage success tracking, Adam optimizer (lr 1e-3), and batch size 128. [medium]

**Success criteria:**

1. **[3cf52c19]** (weight=5) RoboticSequence is defined as a Meta-World task which must complete the following sub-tasks sequentially in a single episode: use a hammer to hammer in a nail (hammer), push an object from one specific place to another (push), remove a bolt from a wall (peg-unplug-side), push an object around a wall (push-wall). If it performs these steps in the correct order, this is counted as a success, otherwise it's attempt it counted as a failure
2. **[37617d8a]** (weight=1) In the RoboticSequence environment, the starting positions and goal conditions are randomly sampled
3. **[2b588e8e]** (weight=1) In the RoboticSequence environment, the Stage ID is encoded as a one-hot vector and provided to the agent
4. **[1b2f259d]** (weight=1) In the RoboticSequence environment, the normalized timestep (i.e. the timestep divided by the maximal number of steps in the environment) is appended to the state vector
5. **[6c9f6163]** (weight=1) In the RoboticSequence environment, the maximal number of steps is defined as 200
6. **[4d94457b]** (weight=1) In the RoboticSequence environment, when the episode ends with success, the agent is provided with the "remaining" reward it would get until the end of the episode; if the last reward was originally $r_t$, the augmented reward is given by $r_t^\prime = \beta r_t (T - t)$, where $\beta$ is defined as $1.5$, and $T$ is the maximal number of steps
7. **[1468553f]** (weight=1) In the RoboticSequence environment, the success rate during training of each sub-task can be measured
8. **[24ca90a0]** (weight=1) In the RoboticSequence environment, the policy and Q-value function are implemented as a 4-layer MLP with 256 neurons each
9. **[9e0dc336]** (weight=1) In the RoboticSequence environment, the policy and Q-value function use Leaky-ReLU activations
10. **[09f91c0f]** (weight=1) In the RoboticSequence environment, the policy and Q-value function have layer normalization only after the first layer
11. **[01a729bf]** (weight=1) In the RoboticSequence environment, the Soft Actor-Critic algorithm has been implemented
12. **[415909bb]** (weight=1) In the RoboticSequence environment, a separate output head is created in the neural networks for each stage, and the stage ID information is used to choose the correct head
13. **[377dd263]** (weight=1) In the RoboticSequence environment, the SAC critic is not regularized

### Subtask 7 of 10: Implement the three knowledge retention methods for NetHack fine-tuning: Kickstarting (KS), Behavioral Cloning (BC), and Elastic Weight Consolidation (EWC). For KS, implement the KL-divergence auxiliary loss on online policy trajectories with coefficient 0.5 and exponential decay 0.99998. For BC, build the static buffer from 8000 NLD-AA trajectories with pre-trained model labels, and implement the KL-divergence auxiliary loss with coefficient 2.0 (no decay). For EWC, compute the diagonal Fisher matrix over 10000 batches from the NLD-AA subset and implement the Fisher-weighted L2 penalty with regularization coefficient 2e6. Disable entropy for all KR methods and ensure KR is applied only to actor parameters (not critic). [hard]

**Success criteria:**

1. **[b13b89e2]** (weight=1) When fine-tuning models in the NetHack environment using either elastic weight consolidation (EWC), behavioral cloning (BS), or kickstarting (KS), the entropy maximization loss is not used when computing the total loss
2. **[5bd83334]** (weight=1) For NetHack the Kickstarting knowledge retention method is implemented; an auxiliary loss is implemented as $\mathcal{L}_{KS}(\theta) = \mathbb{E}_{s \sim \pi_\mathcal{B}_\theta} \left[ D_{KL} \left( \pi_{*}(s) \parallel \pi_{\theta}(s) \right) \right]$, where $\pi_\star$ is the frozen pre-trained model for NetHack from (Tuyls et al., 2023), $\pi_\theta$ is the current model, and $\mathcal{B}_\theta$ is a buffer of states
3. **[bc514fb5]** (weight=1) When fine-tuning models in the NetHack environment using kickstarting (KS), the auxiliary loss is computed on a buffer of data generated by the online policy
4. **[294d8931]** (weight=1) When fine-tuning models in the NetHack environment using kickstarting (KS), the auxiliary loss is scaled by a factor of 0.5 and an exponential decay  of 0.99998 is used, where the coefficient is decayed every training step
5. **[1f53c387]** (weight=1) In the behavioural cloning (BC) implementation for NetHack, before training, a subset of states $\mathcal{S}_{BC}$ is gathered on the 8000 trajectories generated by the AutoAscend algorithm, and a buffer is constructed as $\mathcal{B}_{BC} := \{(s,\pi_\star(s)) : s \in \mathcal{S}_{BC} \}$, i.e., the action that the AutoAscend algorithm took on each of such states is recorded
6. **[623ba7fa]** (weight=1) In the behavioural cloning (BC) implementation for NetHack, when fine-tuning, an auxiliary loss is implemented as $\mathcal{L}_{BC}(\theta) = \mathbb{E}_{s \sim \mathcal{B}_{BC}} \left[ D_{KL} \left( \pi_{*}(s) \parallel \pi_{\theta}(s) \right) \right]$, where $\pi_\star$ is the frozen pre-trained model from (Tuyls et al., 2023), and $\mathcal{B}_{BC}$ is a buffer of data containing states from the AutoAscend algorithm
7. **[eb4004f8]** (weight=1) When fine-tuning models in the NetHack environment using behavioral cloning (BC), the auxiliary loss is scaled by a factor of 2.0. No decay is used
8. **[88c2362c]** (weight=1) For NetHack, the diagonal Fisher matrix can be computed as $F_{ii} = \mathbb{E} [\Delta_\thetal(\theta)_i^2]$, where the expectation is computed using the squared gradients of the loss wrt. each parameter over 10000 batches sampled from the NLD-AA subset of 8000 monk trajectories
9. **[eb31b5b8]** (weight=1) For NetHack, the Elastic Weight Consolidation (EWC) knowledge retention method is implemented; the auxiliary loss is implemented as $\mathcal{L}_{\text{aux}} (\theta) = \sum_i F^i(\theta_\star^i-\theta^i)^2$, where $\theta$ is the weights of the current model, $\theta_\star$ is the weights of the pre-trained model from (Tuyls et al., 2023), and $F$ is the diagonal of the Fisher matrix
10. **[fb4230d6]** (weight=1) When fine-tuning models in the NetHack environment using EWC, a regularization coefficient of $2 \cdot 10^6$ is used
11. **[d0fc7e3c]** (weight=1) For the NetHack environment, the knowledge retention methods are not applied to the parameters of the critic

### Subtask 8 of 10: Train and evaluate all five NetHack conditions (from scratch, vanilla FT, FT+EWC, FT+BC, FT+KS) with 5 seeds each and verify the Section 4 performance results (Figure 3a). Confirm that: (1) the frozen pre-trained baseline achieves ~4.5k average return; (2) FT+KS achieves the highest return (~11k); (3) FT+BC is second highest; (4) vanilla FT degrades to ~1k; (5) FT+EWC roughly matches the frozen baseline. This task covers training execution and result verification for the NetHack main experiment. [hard]

**Success criteria:**

1. **[2009038f]** (weight=1) The pre-trained 30M LSTM model (Tuyls et al., 2023) is evaluated on the NetHack environment
2. **[b51f7910]** (weight=1) The 30M LSTM model (Tuyls et al., 2023) is initialized with random weights and pre-trained from scratch on the NetHack environment using APPO and behavioral cloning (BC) using the original pre-trained 30M LSTM model (Tuyls et al., 2023). The model is trained 5 separate times with 5 unique seeds
3. **[f34e4f40]** (weight=1) The pre-trained 30M LSTM model (Tuyls et al., 2023) is fine-tuned on the NetHack environment using APPO. The model is trained 5 separate times with 5 unique seeds
4. **[636f6d6a]** (weight=1) The pre-trained 30M LSTM model (Tuyls et al., 2023) is fine-tuned with behavioral cloning (BC) on the NetHack environment using APPO. The model is trained 5 separate times with 5 unique seeds
5. **[64b22962]** (weight=1) The pre-trained 30M LSTM model (Tuyls et al., 2023) is fine-tuned with elastic weight consolidation (EWC) on the NetHack environment using APPO. The model is trained 5 separate times with 5 unique seeds
6. **[64b28c7a]** (weight=1) The pre-trained 30M LSTM model (Tuyls et al., 2023) is fine-tuned with kickstarting (KS) on the NetHack environment using APPO. The model is trained 5 separate times with 5 unique seeds
7. **[07ad38d0]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that the pre-trained baseline (Tuyls et al., 2023) achieves an average return around (+-1k) 4.5k
8. **[c6231bba]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that fine-tuning coupled with kickstarting (KS) surpasses the frozen pre-trained baseline (Tuyls et al., 2023) by the end of training, achieving an average return roughly equivalent to (+-1k) 11k
9. **[9c5f4433]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that fine-tuning coupled with kickstarting (KS) achieves the highest average return at the end of training compared to all other methods
10. **[1aeb1f08]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that fine-tuning the pre-trained baseline (Tuyls et al., 2023) results in an average return of 1k by the end of training
11. **[7516943c]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that fine-tuning coupled with behavioral cloning (BC) achieves the second highest average return at the end of training compared to all other methods
12. **[b9a9dcfc]** (weight=1) The recorded metrics for the NetHack experiments in Section 4 show that fine-tuning coupled with elastic weight consolidation (EWC) achieves an average return similar to the frozen  pre-trained baseline by the end of training

### Subtask 9 of 10: Implement the Montezuma's Revenge environment, CNN+RND model architecture, PPO training pipeline, and knowledge retention methods (BC and EWC). Set up the Atari environment from the RND reference implementation with the CNN architecture, RND target/prediction networks outputting 512-dim vectors. Configure PPO with all Table 2 hyperparameters. Implement BC (KL loss on 500-trajectory buffer from a pre-trained agent reaching ~7000 reward) and EWC (Fisher-weighted L2 penalty computed from 500 trajectories). Ensure KR is applied only to actor parameters. Implement evaluation metrics: average return and Room 7 success rate (computed every 5M steps). [hard]

**Success criteria:**

1. **[d8ea9cf5]** (weight=1) The Montezuma's Revenge environment has been imported from https://github.com/jcwleo/random-network-distillation-pytorch
2. **[44ecfe05]** (weight=2) All models for the Montezuma's Revenge environment are based on the architecture from https://github.com/jcwleo/random-network-distillation-pytorch
3. **[5a67161e]** (weight=1) The models trained on the Montezuma's Revenge environment use Random Network Distillation (RND) for training
4. **[3ab393d2]** (weight=1) The models trained on the Montezuma's Revenge environment receive and return vectors of size 512 for both the target network and prediction network
5. **[14dc7245]** (weight=1) The models trained on the Montezuma's Revenge environment use PPO for training, using the implementation from https://github.com/jcwleo/random-network-distillation-pytorch
6. **[ca6edffa]** (weight=1) For constructing the dataset for training the "pre-trained" baseline for Montezuma's Revenge environment, 500 trajectories are sampled from a pre-trained PPO agent with RND that has achieved an episode cumulative reward of around 7000 and has been pre-trained from scratch (not using existing pre-trained weights)
7. **[a6ed1e61]** (weight=1) Fine-tuning models in the Montezuma's Revenge environment using behavioural cloning (BC) has been correctly implemented; an auxiliary loss is implemented as $\mathcal{L}_{BC}(\theta) = \mathbb{E}_{s \sim \mathcal{B}_{BC}} \left[ D_{KL} \left( \pi_{*}(s) \parallel \pi_{\theta}(s) \right) \right]$, where $\pi_{\theta}$ is the current model, $\pi_\star$ is the pre-trained model, and $B_{BC}$ is a buffer of the 500 trajectories computed by the pre-trained PPO agent with RND that achieved an episode cumulative reward of around 7000
8. **[c37de5ab]** (weight=1) For Montezuma's Revenge, the diagonal Fisher matrix can be computed as $F_{ii} = \mathbb{E} [\Delta_\thetal(\theta)_i^2]$, where the expectation is computed using the squared gradients of the loss wrt. each parameter using the 500 trajectories sampled from the pre-trained PPO agent that achieved an episode cumulative reward of around 7000
9. **[1c8fecd4]** (weight=1) For Montezuma's Revenge, the Elastic Weight Consolidation (EWC) knowledge retention method is implemented; the auxiliary loss is implemented as $\mathcal{L}_{\text{aux}} (\theta) = \sum_i F^i(\theta_\star^i-\theta^i)^2$, where $\theta$ is the weights of the current model, $\theta_\star$ is the weights of the pre-trained model, and $F$ is the diagonal of the Fisher matrix
10. **[4bc41c97]** (weight=1) For the Montezuma's Revenge environment, the knowledge retention methods are not applied to the parameters of the critic
11. **[13a214e6]** (weight=1) For the experiments in Section 4 related to Montezuma's Revenge, the average return for a method that has been trained for N steps is computed as the average return over all steps in the trajectory
12. **[dcff0bef]** (weight=1) In the Montezuma's Revenge environment, when starting agents in Room 7, the success rate in Room 7 is computed at achieving at least one of the following: either earn a coin as a reward, acquire a new item, or exit the room through a different passage than the one the agent entered through
13. **[de1df70e]** (weight=1) In the Montezuma's Revenge environment, when training models, the success rate in Room 7 is computed every 5 million training steps

### Subtask 10 of 10: Train and evaluate all four Montezuma's Revenge fine-tuning conditions (from scratch, vanilla FT, FT+BC, FT+EWC) with 5 seeds each and verify the Section 4 and Section 5 results (Figures 5-6). Pre-train a PPO+RND agent from Room 7 onward until ~7000 reward, collect 500 BC trajectories. Run all conditions and track average return and Room 7 success rate. Verify that: (1) FT+BC achieves highest return (~6000); (2) all FT methods outperform from-scratch; (3) EWC return converges around 5e7 steps; (4) vanilla FT Room 7 success drops to ~[X] after 2e7 steps; (5) BC and EWC maintain stable Room 7 success (~[X]); (6) vanilla FT has lowest Room 7 success rate. [hard]

**Success criteria:**

1. **[3b3d3de8]** (weight=1) The pre-trained model is initialized with random weights and pre-trained from scratch on the Montezuma's Revenge environment using PPO with RND until it achieves an episode reward around 7000
2. **[74684ac6]** (weight=1) For the "from scratch" baseline, the pre-trained model is initialized with random weights and pre-trained from scratch on the Montezuma's Revenge environment using PPO with RND. The "from scratch" model is trained 5 separate times with 5 unique seeds
3. **[402dc442]** (weight=1) For the "pre-trained" baseline, the pre-trained model is initialized with random weights and pre-trained from scratch on the Montezuma's Revenge environment, using using PPO with RND and behavioral cloning with 500 trajectories from the "from scratch" model. The"pre-trained" model is trained 5 separate times with 5 unique seeds
4. **[832e0bdc]** (weight=1) The "pre-trained" baseline is fine-tuned on the Montezuma's Revenge environment using PPO with RND. The model is trained 5 separate times with 5 unique seeds
5. **[9e59fb14]** (weight=1) The "pre-trained" baseline is fine-tuned with behavioral cloning (BC) on the Montezuma's Revenge environment using PPO with RND. The model is trained 5 separate times with 5 unique seeds
6. **[a7204cbc]** (weight=1) The "pre-trained" baseline is fine-tuned with elastic weight consolidation (EWC) on the Montezuma's Revenge environment using PPO with RND. The model is trained 5 separate times with 5 unique seeds
7. **[2176d442]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that fine-tuning coupled with behavioural cloning (BC) achieves an average return around 6000 by the end of training
8. **[ca63a2e9]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that all methods fine-tuning coupled with behavioural cloning (BC), vanilla fine-tuning, and fine-tuning coupled with elastic weight consolidation (EWC) achieve an average return higher than the pre-training from scratch baseline by the end of training
9. **[637c9dff]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that the average return converges around 5e7 steps for fine-tuning coupled with elastic weight consolidation (EWC)
10. **[deb0db6c]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that vanilla fine-tuning achieves the lowest success rate in Room 7 compared to all other methods by the end of training
11. **[c075713f]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that the methods fine-tuning coupled with behavioural cloning (BC) and fine-tuning coupled with elastic weight consolidation (EWC) achieve a success rate in Room 7 lower or roughly equivalent to the pre-trained baseline by the end of training
12. **[91e46a34]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that the methods fine-tuning coupled with behavioural cloning (BC) and fine-tuning coupled with elastic weight consolidation (EWC) have a fairly constant success rate in Room 7 throughout training, rarely fluctuating more than 0.75+-0.10
13. **[b69054fc]** (weight=1) The recorded metrics for the Montezuma's Revenge experiments in Section 4 show that the success rate in Room 7 of vanilla fine-tuning falls to roughly 0.55 after 2e7 steps of training

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/ftrl_ara_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: ftrl

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
