# Full Paper Reproduction: rice

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/rice_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/rice_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/rice.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/rice` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/rice_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Set up the four dense MuJoCo environments (Hopper-v3, Walker2d-v3, Reacher-v2, HalfCheetah-v3) with observation normalization where required, implement the PPO policy network, and pretrain a PPO agent on each environment. [easy]

**Success criteria:**

1. **[b60369ed]** (weight=3) Any version of the (MuJoCo) Hopper environment has been correctly set up and can be initialized can be used to run the experiments (further information about this environment in Appendix C.2).
2. **[54ad568e]** (weight=1) The (MuJoCo) Hopper environment is version "Hopper-v3" (further information about this environment in Appendix C.2).
3. **[3dfc9232]** (weight=3) Any version of the (MuJoCo) Walker2d environment has been correctly set up and can be initialized can be used to run the experiments (further information about this environment in Appendix C.2).
4. **[5f77df97]** (weight=1) The (MuJoCo) Walker2d environment is version "Walker2d-v3" (further information about this environment in Appendix C.2).
5. **[d3dceca7]** (weight=1) In the (MuJoCo) Walker2d environment, the observations are normalized when training DRL agents (further information about this environment in Appendix C.2).
6. **[3945867c]** (weight=3) Any version of the (MuJoCo) Reacher environment has been correctly set up and can be initialized can be used to run the experiments (further information about this environment in Appendix C.2).
7. **[22e87ccc]** (weight=1) The (MuJoCo) Reacher environment is version "Reacher-v2" (further information about this environment in Appendix C.2).
8. **[7d4737bb]** (weight=3) Any version of the (MuJoCo) HalfCheetah environment has been correctly set up and can be initialized can be used to run the experiments (further information about this environment in Appendix C.2).
9. **[9396ab08]** (weight=1) The (MuJoCo) HalfCheetah environment is version "HalfCheetah-v3" (further information about this environment in Appendix C.2).
10. **[06a8c8ac]** (weight=2) In the (MuJoCo) HalfCheetah environment, the observations are normalized when training DRL agents (further information about this environment in Appendix C.2).
11. **[c8ce16bb]** (weight=1) For the MuJoCo environments, the policy network agents has been implemented
12. **[a87331ac]** (weight=1) For the MuJoCo environments, code for pretraining the policy network agent on each environment has been setup
13. **[ce49667e]** (weight=2) For each of the MuJoCo environments, a policy network agent has been pretrained, resulting in a pretrained policy network for each MuJoCo environment

### Subtask 2 of 10: Implement the original StateMask (primal-dual) and optimized StateMask (PPO-based with blinding bonus alpha) explanation methods for MuJoCo environments. Implement the mask network that outputs 0 for critical steps and 1 otherwise, the original J(theta) = min|eta(pi)-eta(pi_bar)| objective, and the transformed J(theta) = max eta(pi_bar) objective with configurable alpha. [easy]

**Success criteria:**

1. **[143f314c]** (weight=1) For the MuJoCo environments, the explanation method implementation relies on a mask network that outputs "0" for critical steps and "1" otherwise
2. **[17729bfd]** (weight=1) For the MuJoCo environments, the mask network objective $J(\theta)$ has been implemented to match what is outlined in section 3.3, namely $J(\theta)=\min |\eta(\pi)-\eta(\bar{\pi})|$
3. **[b8d07797]** (weight=1) For the MuJoCo environments, the optimization of the mask network objective of using prime-dual methods has been implemented.
4. **[d3c987e9]** (weight=1) For the MuJoCo environments, the original StateMask Explanation method can be selected as the explanation method during retraining
5. **[dcfd2b61]** (weight=1) For the MuJoCo environments, the original StateMask Explanation method can be selected for generating rollouts (without training)
6. **[29f9e53c]** (weight=2) For the MuJoCo environments, the objective being optimized is $J(\theta)=\max \eta(\bar{\pi})$, as outlined in section 3.3.
7. **[22155807]** (weight=2) For the MuJoCo environments, the reward function is implemented such that an additional reward is given when the mask net outputs "1", as outlined in section 3.3.
8. **[632df4ba]** (weight=1) For the MuJoCo environments, the additional reward given when the mask net outputs "1" is governed by a mutable hyperparameter, i.e., a hyperparameter whose value can be changed (without having to edit the code directly), corresponding to $\alpha$ in the paper. Alternative hyperparameter names are allowed, as long as the functionality remains the same.
9. **[bf075d5c]** (weight=1) For the MuJoCo environments, the optimization of the mask network objective now uses PPO rather than the prime-dual method
10. **[358bcf48]** (weight=1) For the MuJoCo environments, The StateMask ("Ours") Explanation method can be selected as the explanation method during retraining
11. **[e743cd24]** (weight=1) For the MuJoCo environments, The StateMask ("Ours") Explanation method can be selected for generating rollouts (without training)
12. **[48d9a794]** (weight=1) For the MuJoCo environments, the "Random" Explanation method has been implemented as outlined in 4.1, wherein critical steps are identified by randomly selecting previously visited states.
13. **[5a8c16f5]** (weight=1) For the MuJoCo environments, the explanation fidelity score metric has been implemented as outlined in section 4.1 and 4.2: by forcing a given pretrained policy network agent to take random actions starting from each identified critical time step and measuring the average and maximum reward change.

### Subtask 3 of 10: Implement the RICE refining method (mixed initial state distribution + RND exploration bonus) and all three baselines (PPO fine-tuning, StateMask-R, JSRL) for MuJoCo environments. Ensure hyperparameters p (mixing probability) and lambda (RND weight) are configurable. [easy]

**Success criteria:**

1. **[fc13b48a]** (weight=1) For the MuJoCo environments, StateMask fine-tuning, aka "StateMask-R" has been implemented as outlined in section 4.1 and Cheng et al., 2023, i.e. resetting to the identified critical states and continuing training from there.
2. **[6ff262df]** (weight=2) For the MuJoCo environments, code for constructing a mixed initial state distribution by combining default initial states and critical states identified by the "Ours" explanation method has been implemented as described in Section 3.3.
3. **[c5acc159]** (weight=2) For the MuJoCo environments, Random Network Distillation (RND) for exploration has been implemented as outlined in Section 3.3.
4. **[9d9512eb]** (weight=3) For the MuJoCo environments, the refining method has been implemented as outlined in Algorithm 2, integrating the mixed initial state distribution and RND.
5. **[ee6a8328]** (weight=1) For the MuJoCo environments, the refining method has been implemented to support the hyperparameter $\lambda$ to govern the trade-off between task reward and exploration bonus, as outlined in section 3.3. The $\lambda$ hyperparameter must be mutable i.e., a hyperparameter whose value can be changed (without having to edit the code directly). Alternative hyperparameter names are allowed, as long as the functionality remains the same.
6. **[14841e38]** (weight=1) For the MuJoCo environments, the refining method has been implemented to support the hyperparameter $p$, the probability threshold defining the mixed initial state distribution, as evidenced in Algorithm 2.  The $p$ hyperparameter must be mutable i.e., a hyperparameter whose value can be changed (without having to edit the code directly). Alternative hyperparameter names are allowed, as long as the functionality remains the same.
7. **[9f7d0d0f]** (weight=1) For the MuJoCo environments, the "PPO fine-tuning" refinement method has been implemented as outlined in section 4.1, i.e. lowering the learning rate and continuing training with the PPO algorithm.
8. **[1c311868]** (weight=1) For the MuJoCo environments, the Jump-Start Reinforcement Learning ("JSRL") refinement method has been implemented as outlined in section 4.1 and Uchendu et al. (2023), i.e. through initializing the exploration policy $\pi_{e}$ to be equal to the guided policy $\pi_{g}$.

### Subtask 4 of 10: Train StateMask and Optimized StateMask (Ours) on the four dense MuJoCo environments and evaluate Experiment I: compare fidelity scores at K = 10%, 20%, 30%, 40% across 3 seeds, report training time (seconds), and verify that Ours achieves comparable fidelity while training approximately [X]% faster on average. [medium]

**Success criteria:**

1. **[5847ef05]** (weight=1) For each of the non-sparse MuJoCo environments, the "StateMask" explanation method has been trained
2. **[2b13f7a7]** (weight=1) For each of the non-sparse MuJoCo environments, the "StateMask" explanation method has been used to identify the top K most critical time steps. This has been repeated for K = 10%, 20%, 30% and 40%
3. **[d2829f5e]** (weight=1) For each of the the non-sparse MuJoCo environments, for the "StateMask" explanation method, the fidelity score metric has been measured for each K across 500 trajectories
4. **[a8326b10]** (weight=1) For each of the non-sparse MuJoCo environments, the methodology explained in Experiment I using "StateMask" (training "StateMask", identifying the top K most critical time steps, and measuring the fidelity score) has been repeated for a total of 3 different random seeds
5. **[6b2f7d07]** (weight=1) For the non-sparse MuJoCo environments, for the "StateMask" explanation method, code for measuring training time throughout training as outlined in Appendix C.3 and Table 4 has been implemented.
6. **[32bbbf26]** (weight=1) For the non-sparse MuJoCo environments, for the "StateMask" explanation method, training time has been measured throughout as outlined in Section 4.2
7. **[5dc01394]** (weight=1) For each of the non-sparse MuJoCo environments, the "Ours" explanation method has been trained
8. **[6cc090bc]** (weight=1) For each of the non-sparse MuJoCo environments, the "Ours" explanation method has been used to identify the top K most critical time steps. This has been repeated for K = 10%, 20%, 30% and 40%
9. **[e7ea3cdf]** (weight=1) For each of the the non-sparse MuJoCo environments, for the "Ours" explanation method, the fidelity score metric has been measured for each K across 500 trajectories
10. **[5045ef7f]** (weight=1) For each of the non-sparse MuJoCo environments, the methodology explained in Experiment I using "Ours" (training "Ours", identifying the top K most critical time steps, and measuring the fidelity score) has been repeated for a total of 3 different random seeds
11. **[a2fcbf80]** (weight=1) For the non-sparse MuJoCo environments, for the "Ours" explanation method, code for measuring training time throughout training as outlined in Appendix C.3 and Table 4 has been implemented.
12. **[ab5b547a]** (weight=1) For the non-sparse MuJoCo environments, for the "Ours" explanation method, training time has been measured throughout as outlined in Section 4.2
13. **[ba97fafc]** (weight=1) For each environment, the fidelity scores are reported as the mean and standard deviation acrosss 3 seeds
14. **[ca72c6a5]** (weight=1) The fidelity scores reported include all Top-K values of K = 10%, 20%, 30% and 40%
15. **[e834600f]** (weight=3) For the section 4.3 results, the fidelity scores of StateMask and the Optimised StateMask proposed by the paper ("OURS") are generally comparable across the correctly setup non-sparse environments and K's

### Subtask 5 of 10: Run Experiment II on dense MuJoCo environments: refine pretrained PPO agents using RICE (Ours) and all baselines (PPO fine-tuning, StateMask-R, JSRL). Report cumulative reward (mean +/- std across 3 seeds) before and after refining. Verify that RICE achieves the largest improvement, PPO fine-tuning shows marginal improvement, and StateMask-R sometimes degrades performance. [medium]

**Success criteria:**

1. **[3d0f30f8]** (weight=2) In Experiment II, for the MuJoCo environments, for the "Ours" refinement method, the optimized StateMask ("Ours") explanation method proposed in the paper is used as the explanation method.
2. **[caa6183f]** (weight=1) In Experiment II, for the MuJoCo environments, for the "Ours" refinement method, code has been implemented for measuring cumulative reward throughout refinement
3. **[bcc7b87a]** (weight=2) In Experiment II, for the MuJoCo environments, for the "Ours" refinement method, the pretrained policy network agent has been refined
4. **[646b586d]** (weight=2) In Experiment II, for the MuJoCo environments, for the "Ours" refinement method, the performance (cumulative reward) has been measured as the final reward of the refined agent
5. **[2a2b381d]** (weight=1) In Experiment II, for the MuJoCo environments, for the "Ours" refinement method, the performance (cumulative reward) before refinement has been measured
6. **[c844a419]** (weight=2) In Experiment II, for the MuJoCo environments, for the "StateMask-R" refinement method, the pretrained policy network agent has been refined
7. **[862d4b09]** (weight=2) In Experiment II, for the MuJoCo environments, for the "StateMask-R" refinement method, the performance (cumulative reward) has been measured as the final reward of the refined agent
8. **[79acd816]** (weight=2) In Experiment II, for the MuJoCo environments, for the "JSRL" refinement method, the pretrained policy network agent has been refined
9. **[11f8f9a9]** (weight=2) In Experiment II, for the MuJoCo environments, for the "JSRL" refinement method, the performance (cumulative reward) has been measured as the final reward of the refined agent
10. **[f789f789]** (weight=2) In Experiment II, for the MuJoCo environments, for the "PPO fine-tuning" refinement method, the pretrained policy network agent has been refined
11. **[1753a88e]** (weight=2) In Experiment II, for the MuJoCo environments, for the "PPO fine-tuning" refinement method, the performance (cumulative reward) has been measured as the final reward of the refined agent
12. **[9a4fc11e]** (weight=2) For Experiment II, the performance from the "Ours" refinement method brings the largest improvement to the pretrained policy network compared to the other refinement methods
13. **[a03cb5a1]** (weight=1) For Experiment II, the performance from the "PPO fine-tune" refinement method shows only comparatively marginal improvements to the pretrained policy network
14. **[237ad521]** (weight=1) For Experiment II, the performance from the "StateMask-R" refinement method is sometimes worse than the performance of the pretrained policy network

### Subtask 6 of 10: Set up the two sparse MuJoCo environments (SparseHopper, SparseHalfCheetah) and run Experiment II on sparse environments: refine pretrained agents with RICE and all baselines, producing refining curves comparable to Figure 2a. Verify RICE achieves the highest reward (~900 in SparseHopper) at convergence and outperforms all baselines in both sparse environments. [medium]

**Success criteria:**

1. **[e4bb76d7]** (weight=3) Any version of the (MuJoCo) Sparse Hopper environment has been correctly set up and can be initialized can be used to run the experiments.
2. **[74e39b4f]** (weight=1) The (MuJoCo) Sparse Hopper environment is version "Hopper-v3"
3. **[ac87da61]** (weight=3) Any version of the (MuJoCo) Sparse HalfCheetah environment has been correctly set up and can be initialized can be used to run the experiments.
4. **[fb3b2f03]** (weight=1) The (MuJoCo) Sparse HalfCheetah environment is version "HalfCheetah-v3"
5. **[a51b8a8e]** (weight=2) In the (MuJoCo) Sparse HalfCheetah environment, the observations are normalized when training DRL agents (further information about this environment in Appendix C.2).
6. **[3f8c1dd8]** (weight=1) Results have been reported for each of the correctly setup sparse environments, in a format comparable to Figure 2a of the paper.
7. **[ed3b38dd]** (weight=1) The Reward at each refining step is reported for all refinement methods, in a format comparable to Figure 2a of the paper.
8. **[e9b855d2]** (weight=2) For Experiment II, the "Ours" refinement method has been shown to achieve highest reward (around ~900 in Figure 2a) at the end of the refinement process compared to the other refinement methods for both sparse environments.
9. **[2784c2ec]** (weight=2) For Experiment II, the "Ours" refinement method has been shown to achieve the highest rewards (around ~900 in Figure 2a) earlier in the refinement process (more efficiently) compared to the other refinement methods for both sparse environments.

### Subtask 7 of 10: Reproduce Experiment V p and lambda sensitivity: sweep mixing probability p in {0, 0.25, 0.5, 0.75, 1.0} and RND exploration coefficient lambda in {0, 0.1, 0.01, 0.001} across all environments. Verify that mixed p values (0 < p < 1) outperform pure initialization (p=0 or p=1), and that lambda > 0 improves performance over lambda = 0. [hard]

**Success criteria:**

1. **[5dfcfd17]** (weight=1) For the MuJoCo dense environments, following the methodology described for Experiment V, Experiment II has been repeated with $p \in \{0, 0.25, 0.5, 0.75, 1\}$, at a fixed $\lambda$ value and the final reward has been measured.
2. **[329a8def]** (weight=1) For the MuJoCo dense environments, following the methodology described for Experiment V, Experiment II has been repeated with $\lambda \in \{0, 0.1, 0.01, 0.001\}$, at a fixed $p$ value and the final reward has been measured.
3. **[1e850be3]** (weight=1) For the selfish mining environment, following the methodology described for Experiment V, Experiment II has been repeated with $p \in \{0, 0.25, 0.5, 0.75, 1\}$, at a fixed $\lambda$ value and the final reward has been measured.
4. **[01c9dd08]** (weight=1) For the selfish mining environment, following the methodology described for Experiment V, Experiment II has been repeated with $\lambda \in \{0, 0.1, 0.01, 0.001\}$, at a fixed $p$ value and the final reward has been measured.
5. **[39f39967]** (weight=1) For the network defence environment, following the methodology described for Experiment V, Experiment II has been repeated with $p \in \{0, 0.25, 0.5, 0.75, 1\}$, at a fixed $\lambda$ value and the final reward has been measured.
6. **[fec7f4e9]** (weight=1) For the network defence environment, following the methodology described for Experiment V, Experiment II has been repeated with $\lambda \in \{0, 0.1, 0.01, 0.001\}$, at a fixed $p$ value and the final reward has been measured.
7. **[35e38a34]** (weight=1) For the autonomous driving environment, following the methodology described for Experiment V, Experiment II has been repeated with $p \in \{0, 0.25, 0.5, 0.75, 1\}$, at a fixed $\lambda$ value and the final reward has been measured.
8. **[adc60774]** (weight=1) For the autonomous driving environment, following the methodology described for Experiment V, Experiment II has been repeated with $\lambda \in \{0, 0.1, 0.01, 0.001\}$, at a fixed $p$ value and the final reward has been measured.
9. **[0a2fc041]** (weight=2) The experimental results for Experiment V show that refinement performance is lowest when $p=0$ or $p=1$
10. **[da43435e]** (weight=2) The experimental results for Experiment V show that refinement performance noticeably improves when $\lambda > 0$

### Subtask 8 of 10: Reproduce Experiment IV (cross-algorithm refining): pretrain a SAC agent on dense Hopper for 1M steps, convert it to a PPO-compatible policy via GAIL imitation learning, then refine using RICE and all baselines (SAC fine-tuning, PPO fine-tuning, StateMask-R, JSRL). Verify that RICE outperforms all baselines including SAC fine-tuning, and that PPO fine-tuning achieves higher reward than SAC fine-tuning. [hard]

**Success criteria:**

1. **[3dd86059]** (weight=1) Code for pretraining a Soft Actor Critic (SAC) network agent on the dense MuJoCo Hopper environment has been implemented
2. **[42a4230a]** (weight=1) Code for measuring reward throughout pretraining and refinement has been implemented
3. **[b4908b09]** (weight=2) A pretrained agent trained with Soft Actor Critic (SAC) for 1M steps on the dense MuJoCo Hopper environment has been acquired as outlined in section 4.2
4. **[3cbadd76]** (weight=1) Code for applying Generative Adversarial Imitation Learning (GAIL) to a given SAC network agent has been implemented
5. **[aea05231]** (weight=1) An approximated policy network version of the pretrained SAC agent has been acquired using Generative Adversarial Imitation Learning (GAIL) as outlined in section 4.2
6. **[49ff5227]** (weight=1) The pretrained SAC agent has been refined by further fine-tuning with SAC for 1M steps
7. **[81818e53]** (weight=1) The policy network version of the pretrained SAC agent obtained via GAIL has been refined by using the "PPO fine-tuning" refinement method for 1M steps
8. **[4b6457bc]** (weight=1) The paper's proposed explanation method has been used to identify critical steps.
9. **[4d1ff848]** (weight=1) The policy network version of the pretrained SAC agent obtained via GAIL has been refined by using the "JSRL" refinement method for 1M steps
10. **[85c81232]** (weight=1) The policy network version of the pretrained SAC agent obtained via GAIL has been refined by using the "StateMask-R" refinement method for 1M steps
11. **[f40e9fd2]** (weight=1) The policy network version of the pretrained SAC agent obtained via GAIL has been refined by using the proposed "Ours" refinement method for 1M steps
12. **[56813d1a]** (weight=1) For Experiment IV, reward has been measured throughout pretraining and refinement for all considered methods
13. **[df6a98da]** (weight=3) For Experiment IV, the reward measured shows that, by the end of the refinement phase, the proposed "Ours" refining method achieves higher rewards than the other refining methods when refining a pretrained SAC agent on the dense MuJoCo Hopper environment
14. **[ddce5c57]** (weight=2) For Experiment IV, the reward measured shows that, by the end of refinement phase, refinement with "PPO-finetuning" achieves higher rewards than refinement with SAC-finetuning on the dense MuJoCo Hopper environment

### Subtask 9 of 10: Run Experiment III (explanation quality ablation) on MuJoCo environments: fix the RICE refining method and vary the explanation source (Random, StateMask, Ours), comparing downstream refining performance (cumulative reward). Verify that refining with StateMask or Ours explanations outperforms refining with Random explanations, confirming that higher-fidelity explanations yield better refining outcomes. [hard]

**Success criteria:**

1. **[217cd73d]** (weight=2) For the MuJoCo environments, the "Random" explanation method has been utilized to identify the critical step to refine from
2. **[5ce51a77]** (weight=1) For the MuJoCo environments, for the "Random" explanation method, code has been implemented for measuring cumulative reward throughout refinement
3. **[35620546]** (weight=1) For the MuJoCo environments, the paper's proposed refinement method ("Ours") has been used as the refinement method to refine the pretrained policy network from the critical steps identified from the "Random" explanation method
4. **[122fccfd]** (weight=2) For the MuJoCo environments, for the "Random" explanation method, the pretrained policy network agent has been refined
5. **[9b2cc875]** (weight=2) For the MuJoCo environments, for the "Random" explanation method, the performance (cumulative reward) has been measured as the final reward of the refined agent
6. **[ad2b5ff0]** (weight=2) For the MuJoCo environments, the "StateMask" explanation method has been utilized to identify the critical step to refine from
7. **[a2cf487b]** (weight=2) For the MuJoCo environments, for the "StateMask" explanation method, the pretrained policy network agent has been refined
8. **[e21bb1b9]** (weight=2) For the MuJoCo environments, for the "StateMask" explanation method, the performance (cumulative reward) has been measured as the final reward of the refined agent
9. **[5b79083b]** (weight=2) For the MuJoCo environments, the "Ours" explanation method has been utilized to identify the critical step to refine from
10. **[c477bf52]** (weight=2) For the MuJoCo environments, for the "Ours" explanation method, the pretrained policy network agent has been refined
11. **[0e027908]** (weight=2) For the MuJoCo environments, for the "Ours" explanation method, the performance (cumulative reward) has been measured as the final reward of the refined agent
12. **[3829943a]** (weight=2) From the results of Experiment III, the performance measures show that refining from the "StateMask" or "Ours" explanation methods outperforms refining from the "Random" explanations, as shown in the "Fix Refine; Vary Explanation Methods" portion of Table 1.

### Subtask 10 of 10: Reproduce Experiment V alpha sensitivity: sweep the mask network blinding bonus alpha in {0.01, 0.001, 0.0001} and re-run Experiment I fidelity measurement on all environments. Verify that fidelity scores are insensitive to alpha (scores remain similar across all alpha values). [hard]

**Success criteria:**

1. **[211d1077]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") across the correctly setup MuJoCo dense environments for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the fidelity score for each value of alpha has been measured
2. **[e6002227]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") across the correctly setup MuJoCo dense environments for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the final reward has been measured
3. **[c75ccbdd]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the selfish mining environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the fidelity score for each value of alpha has been measured
4. **[390ef180]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the selfish mining environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the final reward has been measured
5. **[6301e9da]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the network defence environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the fidelity score for each value of alpha has been measured
6. **[5c97f0be]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the network defence environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the final reward has been measured
7. **[4e0b4788]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the autonomous driving environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the fidelity score for each value of alpha has been measured
8. **[46204d98]** (weight=1) Following the methodology described for Experiment V, Experiment I has been repeated for the proposed optimised StateMask explanation method ("Ours") for the autonomous driving environment for $\alpha \in \{0.01, 0.001, 0.0001\}$, and the final reward has been measured
9. **[e31d3e10]** (weight=2) The experimental results for Experiment V show that the proposed explanation method ("Ours") is not sensitive to changes in $\alpha$, with the fidelity score remaining comparable across the tested different values of $\alpha$

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/rice_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: rice

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
