# Full Paper Reproduction: fre

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/fre_ara_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/fre_ara_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the paper's **structured research artifact (ARA)**. You have NO access to the original paper PDF or its companion GitHub repository.

**ARA artifact location**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/artifacts/fre`

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

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/fre_ara_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the FRE encoder-decoder architecture. Build the transformer-based variational encoder with reward discretization into 32 bins, learned reward and state embeddings, permutation-invariant attention (no positional embeddings), and a variational bottleneck producing a Gaussian latent z. Implement the MLP decoder that independently predicts rewards for query states given z. Verify the architecture matches the hyperparameters specified in Appendix A. [easy]

**Success criteria:**

1. **[ea36bca4]** (weight=1) The FRE implementation consists of an Encoder-Decoder network, and a FRE-conditioned IQL policy
2. **[04d679d0]** (weight=1) The FRE Encoder network has been implemented such that the input scalar reward is discretized into 32 bins by rescaling the reward to [0,1] and then multiplying by 32 and flooring to the nearest integer
3. **[7297f42f]** (weight=1) The FRE Encoder network has been implemented such that the discretized reward is is mapped to a continuous vector representation using a learned embedding table
4. **[a9ad5a0c]** (weight=1) The FRE Encoder network has been implemented such that the the environment state projected into an embedding using a learned linear transformation
5. **[4afafbc9]** (weight=1) The FRE Encoder network has been implemented such that for each state, the reward embedding is concatenated to end of the state embedding before the set of reward-labeled states is passed through the encoder
6. **[90b8884f]** (weight=1) The FRE Encoder has been implemented such that it takes a set of states labeled with their scalar rewards as input
7. **[e812f3c1]** (weight=1) The FRE Encoder has been implemented such that it uses a permutation invariant transformer as the main architecture.
8. **[b57031ba]** (weight=1) The FRE Encoder has been implemented such that the transformer does not use a causal mask on its attention, such that each input token can attend to any other input token.
9. **[17bdcdac]** (weight=1) The FRE encoder has been implemented such that positional embeddings are not used in the transformer
10. **[aa264dc2]** (weight=1) The FRE encoder has been implemented using the hyper-parameters specified in Appendix A
11. **[0748e789]** (weight=1) The FRE Decoder has been implemented such that it uses a feedforward neural network as the main architecture.
12. **[6a54735c]** (weight=1) The FRE Decoder has been implemented such that it independently predicts the reward for a single input state, given a shared latent encoding z
13. **[6d38f122]** (weight=1) The FRE Decoder has been implemented using the hyper-parameters specified in Appendix A

### Subtask 2 of 10: Implement the FRE-conditioned IQL policy network and the full FRE training pipeline. The policy must include an actor, critic, and value function conditioned on the latent z by concatenation. Implement the information-bottleneck ELBO loss (Eq. 6) for encoder-decoder training. Implement the strided training procedure where the encoder-decoder is first trained and then frozen before the IQL policy is trained on FRE-conditioned rewards. Verify policy hyperparameters match Appendix A. [easy]

**Success criteria:**

1. **[6b6edf6b]** (weight=1) The FRE-conditioned policy network has been implemented such that it includes an actor, critic, value, and target critic network
2. **[40d26271]** (weight=1) The FRE-conditioned policy network has been implemented such that the RL components are conditioned on some latent variable z produced by the FRE encoder
3. **[95ebb4b4]** (weight=1) The FRE-conditioned policy network has been implemented such that the actor predicts a Gaussian distribution over actions (mean and log std)
4. **[143af012]** (weight=1) The FRE-conditioned policy has been implemented using the hyper-parameters specified in Appendix A
5. **[bad4958f]** (weight=1) Code has been implemented such that FRE training is strided: In the first phase the encoder-decoder is trained. In the second phase, the encoder is kept frozen while its outputs are used to condition the IQL policy. The IQL policy is trained during this second phase. The decoder is not used in the second phase.
6. **[15d902cd]** (weight=1) Code has been implemented such that when training the FRE encoder-decoder, the variational lower bound outlined in equation (6) is used as the loss function to optimize, or equivalent implementations.
7. **[8b30922a]** (weight=1) Code has been implemented such that when training the FRE encoder-decoder, the states sampled for decoding and the states sampled for encoding are sampled separately, such that the states used for decoding and the states used for encoding are different.
8. **[d922ee95]** (weight=1) Code has been implemented such that when training the FRE-conditioned policy using implicit Q-learning, the critic is updated with an MSE loss to the Bellman target: r + discount * mask * next_value
9. **[422ffe1f]** (weight=1) Code has been implemented such that when training the FRE-conditioned policy using implicit Q-learning, the value function is updated with an expectile regression objective on the critic's Q-values
10. **[5ff98598]** (weight=1) Code has been implemented such that when training the FRE-conditioned policy using implicit Q-learning, the actor is updated via advantage-weighted regression (AWR)
11. **[31e4d8ce]** (weight=1) Code has been implemented such that when training the FRE-conditioned policy using implicit Q-learning, after the critic update, the target critic is updated via a soft update rule from the critic params and previous target critic params.
12. **[f0ab7926]** (weight=1) Code has been implemented such that when training the FRE-conditioned policy using implicit Q-learning, the output z from the frozen encoder is concatenated to the current observation before feeding them into the actor, critic, target critic and value networks
13. **[29cebba5]** (weight=1) Code has been implemented such that when training a FRE agent, reward functions are sampled from some prior reward distribution

### Subtask 3 of 10: Implement the three baseline agent architectures: GC-IQL (goal-conditioned IQL with actor/critic/value, Gaussian actor, and sparse goal-reaching reward), GC-BC (3-hidden-layer MLP with Gaussian output and discretized goal conditioning), and OPAL (permutation-invariant trajectory encoder producing latent z, MLP decoder primitive policy, and hierarchical meta-controller). Implement training procedures for each baseline including OPAL's sub-trajectory autoencoding loss. [easy]

**Success criteria:**

1. **[4bbda5e1]** (weight=1) The GC-IQL model has been implemented such that it includes an actor, critic, value, and target critic network
2. **[d1495479]** (weight=1) The GC-IQL model has been implemented such that the actor predicts a Gaussian distribution over actions (mean and log std)
3. **[55e9351f]** (weight=1) The GC-IQL model has been implemented such that it is goal-conditioned by concatenating the current observation with the desired goal before feeding into the networks
4. **[83fd90f6]** (weight=1) The GC-BC model has been implemented such that it is a MLP with three hidden layers of size 512
5. **[620a2b18]** (weight=1) The GC-BC model has been implemented such that it predicts a gaussian distribution over actions, with two outputs, a mean action and the log of the standard deviation
6. **[714d7e4a]** (weight=1) The GC-BC model has been implemented such that the log of the standard deviation is clamped with a lower bound of -5
7. **[d297b5ab]** (weight=1) The GC-BC model has been implemented such that ReLU is applied between each hidden layer
8. **[424bb63c]** (weight=1) The GC-BC model has been implemented such that layer normalization is applied before each activation function
9. **[b4c6e00e]** (weight=1) The OPAL method has been implemented such that it consists at minimum of an encoder $q_{\phi}(z\mid\tau)$ and a latent-conditioned decoder (primitive policy) $\pi_{\theta}(a\mid s,z)$
10. **[0389ff82]** (weight=1) The OPAL encoder has been implemented such that it reads a sub-trajectory of length $c$, consisting of $(s_{t}, a_{t})$ pairs, and produces parameters of a latent distribution (e.g. mean $\mu_{z}$ and log-standard-deviation $\sigma_{z}$).
11. **[c41ecad0]** (weight=1) The OPAL encoder has been implemented such that it uses a permutation invariant transformer to process the $c$ timesteps and output the latent distribution parameters.
12. **[7b768bcc]** (weight=1) The OPAL encoder has been implemented such that it represents $q_{\phi}(z\mid\tau)$ as a Gaussian distribution parameterized by $(\mu_{z}^{\mathrm{enc}}, \sigma_{z}^{\mathrm{enc}})$ for the latent variable $z$.
13. **[b6fbd20b]** (weight=1) The OPAL decoder has been implemented such that it is a latent-conditioned policy that takes current state $s$ and latent $z$, and outputs a Gaussian distribution over actions, parameterized by $(\mu_{a},\sigma_{a})$.
14. **[caaf32fc]** (weight=1) Code has been implemented such that, to train OPAL agents, sub-trajectories of some length c can be sampled from the offline dataset (e.g. c=10), forming the data used to learn OPAL's encoder and decoder (primitive policy). No reward information is used at this stage.
15. **[2507c345]** (weight=1) Code has been implemented such that, to train OPAL agents, the OPAL autoencoding objective is used: maximizing log-likelihood of actions conditioned on latent $z$ and state, with a KL penalty to keep $q_\phi(z|\tau)$ close to $\rho_\omega(z|s_0)$.

### Subtask 4 of 10: Set up the AntMaze (antmaze-large-diverse-v2) and ExORL (cheetah-RND, walker-RND) datasets and environments. Implement the three reward function families for AntMaze: singleton goal-reaching rewards (with XY discretization into 32 bins), random linear reward functions (with weight normalization and bias), and random MLP reward functions (with 2-hidden-layer architecture). Implement ExORL-specific reward families with physics information appended per Appendix C.2. [medium]

**Success criteria:**

1. **[595c44a3]** (weight=1) Code has been implemented such that the `antmaze-large-diverse-v2` dataset from D4RL can be used for offline training of sequential decision making agents
2. **[5b3ccceb]** (weight=1) Code has been implemented such that the D4RL Ant Maze environment (https://github.com/Farama-Foundation/D4RL/blob/71a9549f2091accff93eeff68f1f3ab2c0e0a288/d4rl/locomotion/ant.py or equivalent) can be used for online evaluation of sequential decision making agents
3. **[bccaf966]** (weight=1) Code has been implemented such that the `cheetah` (RND) dataset from ExORL (https://github.com/denisyarats/exorl)  can be used for offline training of sequential decision making agents
4. **[15a0dc98]** (weight=1) Code has been implemented such that environments from the `cheetah` domain from the custom DeepMind Control Suite ExORL environments (https://github.com/denisyarats/exorl/tree/main/custom_dmc_tasks) can be used for online evaluation of sequential decision making agents
5. **[2b14e66b]** (weight=1) Code has been implemented such that the `walker` (RND) dataset from ExORL (https://github.com/denisyarats/exorl) can be used for offline training of sequential decision making agents
6. **[534f0b86]** (weight=1) Code has been implemented such that environments from the `walker` domain from custom DeepMind Control Suite ExORL environments (https://github.com/denisyarats/exorl/tree/main/custom_dmc_tasks) can be used for online evaluation of sequential decision making agents
7. **[f9cc6afc]** (weight=1) Code has been implemented such that the observation space's XY coordinates are discretized into 32 bins for input to FRE agents trained on Ant Maze dataset
8. **[2ed48cb3]** (weight=1) Code has been implemented such that the additional physics information outlined in Appendix C.2 is appended to the environment state when training the FRE encoder on the ExORL `cheetah` and `walker` (RND) datasets
9. **[425c9fc8]** (weight=1) Code has been implemented such that, when applying singleton goal-reaching reward functions to the trajectories of the `antmaze-large-diverse-v2` dataset, a goal is selected as a random state from the dataset with a probability of 0.2, a future state within the same trajectory with a probability of 0.5 and a completely random different state with a probability of 0.3
10. **[9d761158]** (weight=1) Code has been implemented such that when applying singleton goal-reaching reward functions to the trajectoreis of the `antmaze-large-diverse-v2` dataset, a reward of -1 is assigned at every step unless the agent has reached the goal state.
11. **[d2ad5f82]** (weight=1) Code has been implemented such that when applying random linear reward functions to the trajectories of the `antmaze-large-diverse-v2` dataset, the random vectors defining the functions are sampled from a uniform distribution bound between -1 and 1.
12. **[76cccc3d]** (weight=1) Code has been implemented such that when applying random linear reward functions to the trajectories of the `antmaze-large-diverse-v2` dataset, a random binary mask with 0.9 probability of 0 is applied to the random vector defining the reward function.
13. **[b8b9bd34]** (weight=1) Code has been implemented such that when appying random MLP reward functions to the trajectories of `antmaze-large-diverse-v2` dataset, the random MLPs consist of two linear layers, mapping from the state dimension to a hidden dimension of 32, and from 32 to and output dimension of 1.
14. **[b2fddd01]** (weight=1) Code has been implemented such that when appying random MLP reward functions to the trajectories of `antmaze-large-diverse-v2` dataset, the parameters of the random MLPs are sampled using a normal distribution scaled by the average dimension of the respective layer.

### Subtask 5 of 10: Train a single FRE-all agent on antmaze-large-diverse-v2 with the uniform 1/3 mixture prior over goal-reaching, random linear, and random MLP reward families. Implement the ant-goal-reaching evaluation task with its reward specification. Evaluate the FRE-all agent on ant-goal-reaching over 5 seeds and 20 episodes per seed. Also train and evaluate FB and SF baselines on AntMaze goal-reaching to compare sample efficiency (FRE uses 32 samples vs FB/SF using 5120). [medium]

**Success criteria:**

1. **[df64e51f]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-all prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
2. **[8d4bd046]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-all prior rewards distribution, there is an equal 0.33, 0.33, 0.33 probability of sampling a singleton goal-reaching reward function, a random linear reward functions or a random mlp reward function for each training trajectory.
3. **[64d49648]** (weight=1) A FRE agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset using the FRE-all prior rewards distribution
4. **[66e8abac]** (weight=1) The `ant-goal-reaching` evaluation task has been implemented such that the agent is evaluated on the 5 reward functions outlined in addendum.md
5. **[d9bf8c02]** (weight=1) The `ant-goal-reaching` evaluation task has been implemented such that the average cumulative reward across the 5 reward functions is used as the evaluation metric
6. **[f5dc7467]** (weight=1) The `ant-goal-reaching` evaluation task has been implemented such that the goal is considered reached if an agent reaches within a distance of 2 from the target position.
7. **[f4430c7e]** (weight=1) The `ant-goal-reaching` evaluation task has been implemented such that the agent receives a reward of -1 at each timestep until it successfully reaches the goal.
8. **[ca9b0276]** (weight=1) Code has been implemented such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-all can been evaluated on `ant-goal-reaching`
9. **[d21d6d68]** (weight=1) Code has been executed such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-all has been evaluated over 5 seeds with 20 episodes per seed on `ant-goal-reaching`.
10. **[14d5ca37]** (weight=1) Code has been implemented such that an FB agent can be trained on the Ant Maze `antmaze-large-diverse-v2` dataset
11. **[6db428ff]** (weight=1) An FB agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset
12. **[fa867daf]** (weight=1) Code has been implemented such that an FB agent trained on `antmaze-large-diverse-v2` can been evaluated on `ant-goal-reaching`
13. **[599da9c6]** (weight=1) Code has been executed such that an FB agent trained on `antmaze-large-diverse-v2` has been evaluated over 5 seeds with 20 episodes per seed on `ant-goal-reaching`
14. **[d3c7236a]** (weight=1) Code has been implemented such that FB agents can be trained using the https://github.com/facebookresearch/controllable_agent codebase or a fork of it

### Subtask 6 of 10: Set up the Kitchen (kitchen-complete-v0) dataset and environment. Implement Kitchen-specific reward functions. Train FRE-all, FB, SF, OPAL, GC-IQL, and GC-BC agents on Kitchen. Implement the kitchen evaluation task with sparse binary rewards. Evaluate all agents over 5 seeds and 20 episodes per seed. Verify that Table 1 aggregate results hold: FRE matches or outperforms all baselines across goal-reaching tasks (ant, exorl, kitchen) and dominates on non-goal-reaching tasks. [medium]

**Success criteria:**

1. **[4eb72ad4]** (weight=1) Code has been implemented such that the "kitchen-complete-v0" dataset from D4RL can be used for offline training of sequential decision making agents
2. **[190df881]** (weight=1) Code has been implemented such that the D4RL Kitchen environment (https://github.com/Farama-Foundation/D4RL/tree/71a9549f2091accff93eeff68f1f3ab2c0e0a288/d4rl/kitchen or equivalent) can be used for online evaluation of sequential decision making agents
3. **[2eb7183e]** (weight=1) Code has been implemented such that when training a FRE agent on the `kitchen-complete-v0` dataset using the FRE-all prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
4. **[83202f54]** (weight=1) Code has been implemented such that when training a FRE agent on the `kitchen-complete-v0` dataset using the FRE-all prior rewards distribution, there is an equal 0.33, 0.33, 0.33 probability of sampling a singleton goal-reaching reward function, a random linear reward functions or a random mlp reward function for each training trajectory.
5. **[4c9cfa23]** (weight=1) A FRE agent has been trained on the `kitchen-complete-v0` dataset using the FRE-all prior rewards distribution
6. **[bb2371d7]** (weight=1) The `kitchen` evaluation task has been implemented such that the agent is evaluated on the 7 standard tasks of the Franka Kitchen environment: `bottom-burner`, `kettle`, `light-switch`, `microwave`, `slide-cabinet`, `hinge-cabinet`, `top-burner`
7. **[3fc9b62f]** (weight=1) The `kitchen` evaluation task has been implemented such that the sparse rewards from the 7 standard tasks of the Franka Kitchen environment are used as the reward functions
8. **[c46c155a]** (weight=1) Code has been implemented such that a FRE agent trained on the `kitchen-complete-v0` dataset with the prior reward distribution referred to as FRE-all can been evaluated on `kitchen`
9. **[a8265cc7]** (weight=1) Code has been executed such that a FRE agent trained on the `kitchen-complete-v0` dataset with the prior reward distribution referred to as FRE-all has been evaluated over 5 seeds with 20 episodes per seed on `kitchen`.
10. **[2f2d443f]** (weight=1) The outcome of the evaluation shows that on most goal-reaching tasks (at least 3 of ant-goal-reaching, exorl-cheetah-goals, exorl-walker-goals, kitchen), the performance of the FRE agent is significantly higher than the performance of the SF and FB baselines, as discussed in section 5.2 of the paper
11. **[081c9d9f]** (weight=1) The outcome of the evaluation shows that on most goal-reaching tasks (at least 3 of ant-goal-reaching, exorl-cheetah-goals, exorl-walker-goals, kitchen), the performance of the FRE agent is not significantly lower than the performance of GC-IQL and GC-BC baselines, as discussed in section 5.2 of the paper
12. **[6ff5f645]** (weight=1) The outcome of the evaluation shows that the performance of the FRE agent is competitive (either top or joint top performance) on at least 4 of (ant-directional, ant-random-simplex, ant-path-loop, ant-path-edges, ant-path-center) when compared to all of the SF, FB, GC-IQL, GC-BC and OPAL baselines, as discussed in section 5.2 of the paper
13. **[0a57fe73]** (weight=1) The outcome of the evaluation shows that on average, the FRE agent significantly outperforms the OPAL agent, as discussed in section 5.2 of the paper.
14. **[2f455b0f]** (weight=2) The outcome of the evaluation shows or implies that the FRE agent trained with the augmented FRE-hint prior reward distribution outperforms the FRE agent trained on the vanilla FRE prior reward distribution on all of {ant-directional, cheetah-velocity, walker-velocity} evaluation tasks, as shown in the paper in section 5.4 and Figure 6

### Subtask 7 of 10: Implement the ant-directional and ant-random-simplex evaluation tasks with their reward specifications. Train GC-IQL, GC-BC, and OPAL baselines on antmaze-large-diverse-v2. Evaluate the FRE-all agent (from T05) and all baselines on ant-directional and ant-random-simplex over 5 seeds and 20 episodes per seed. Verify that FRE-all outperforms goal-conditioned baselines (GC-IQL, GC-BC) on non-goal-reaching tasks and outperforms OPAL overall. [hard]

**Success criteria:**

1. **[53a057fc]** (weight=1) The `ant-directional` evaluation task has been implemented such that the agent is evaluated on the 4 reward functions outlined in addendum.md
2. **[e6193543]** (weight=1) The `ant-directional` evaluation task has been implemented such that the average cumulative reward across the 4 reward functions is used as the evaluation metric
3. **[68f27cfa]** (weight=1) The `ant-directional` evaluation task has been implemented such the reward is scaled by how much the agent's velocity aligns with the target direction, utilizing a dot product.
4. **[8a6209c8]** (weight=1) The `ant-random-simplex` evaluation task has been implemented such that the agent is evaluated on the 5 seeded opensimplex height and velocity preferences as outlined in addendum.md
5. **[2ff868ca]** (weight=1) The `ant-random-simplex` evaluation task has been implemented such that the average cumulative reward across the 5 seeded tasks is used as the evaluation metric
6. **[3b6b5d48]** (weight=1) Code has been implemented such that an GC-IQL agent can be trained on the Ant Maze `antmaze-large-diverse-v2` dataset
7. **[f4f6c096]** (weight=1) An GC-IQL agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset
8. **[1c9a402d]** (weight=1) Code has been implemented such that an GC-BC agent can be trained on the Ant Maze `antmaze-large-diverse-v2` dataset
9. **[65f07ab6]** (weight=1) An GC-BC agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset
10. **[3d7c6335]** (weight=1) Code has been implemented such that an OPAL agent can be trained on the Ant Maze `antmaze-large-diverse-v2` dataset
11. **[617c421b]** (weight=1) An OPAL agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset
12. **[448f277f]** (weight=1) Code has been implemented such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-all can been evaluated on `ant-directional`
13. **[32f02dcc]** (weight=1) Code has been executed such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-all has been evaluated over 5 seeds with 20 episodes per seed on `ant-directional`.
14. **[2839bbbb]** (weight=1) Code has been implemented such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-all can been evaluated on `ant-random-simplex`

### Subtask 8 of 10: Reproduce the reward family diversity ablation (Table 4 / Figure 5) on AntMaze. Train seven FRE agent variants on antmaze-large-diverse-v2: FRE-goals, FRE-lin, FRE-mlp, FRE-goal-lin, FRE-goal-mlp, FRE-lin-mlp, and FRE-all. Each variant uses the correct prior mixture probabilities. Evaluate all seven on the four AntMaze evaluation task categories (goal-reaching, directional, random-simplex, path tasks) over 5 seeds. Verify that FRE-all achieves the highest total aggregate score and that performance scales with reward diversity. [hard]

**Success criteria:**

1. **[8cd85ad2]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-goals prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
2. **[61a28b5f]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-goals prior rewards distribution, only singleton goal-reaching reward functions are sampled and used for each training trajectory.
3. **[b40be6bd]** (weight=1) A FRE agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset using the FRE-goals prior rewards distribution
4. **[61af561b]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-lin prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
5. **[1cc28c97]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-lin prior rewards distribution, only random linear reward functions are sampled and used for each training trajectory.
6. **[6e6558f9]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-mlp prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
7. **[b08d7709]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-mlp prior rewards distribution, only random MLP reward functions are sampled and used for each training trajectory.
8. **[03cec4d5]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-lin-mlp prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
9. **[c9914ca1]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-lin-mlp prior rewards distribution, there is an equal 0.5, 0.5 probability of sampling a random linear reward functions or a random mlp reward function for each training trajectory.
10. **[1b4a1806]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-goal-mlp prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
11. **[3963a475]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-goal-lin prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
12. **[5f01970b]** (weight=1) The outcome of the evaluation shows that the FRE agent trained with the FRE-all prior reward distribution achieves the highest average score compared to FRE agents trained with any of {FRE-goals, FRE-lin, FRE-mlp, FRE-lin-mlp, FRE-goal-mlp, FRE-goal-lin} prior reward distributions, as discussed in section 5.3 of the paper and shown in Table 4.
13. **[4860910a]** (weight=1) The outcome of the evaluation shows that the FRE agent trained with the FRE-all prior reward distribution either outperforms or matches the performance of FRE agents trained with any of {FRE-goals, FRE-lin, FRE-mlp, FRE-lin-mlp, FRE-goal-mlp, FRE-goal-lin} prior reward distributions on all of the individual tasks (antmaze-goal-reaching, antmaze-directional, antmaze-random-simplex, and antmaze-path-all, which is the average performance on antmaze-path-loop, antmaze-path-edges and antmaze-path-center), as discussed in section 5.3 of the paper and shown in Table 4.

### Subtask 9 of 10: Train FRE-all agents on ExORL cheetah (RND) and walker (RND) datasets. Implement the exorl-cheetah-velocity, exorl-walker-velocity, exorl-cheetah-goals, and exorl-walker-goals evaluation tasks. Train FB, SF, OPAL, GC-IQL, and GC-BC baselines on both ExORL domains. Evaluate all agents on velocity and goals tasks over 5 seeds and 20 episodes per seed. Verify FRE outperforms SF/FB on goal-reaching tasks with 160x fewer samples and outperforms all baselines on velocity tasks. [hard]

**Success criteria:**

1. **[5508cfda]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `cheetah` (RND) dataset using the FRE-all prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
2. **[a51dc0ea]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `cheetah` (RND) dataset using the FRE-all prior rewards distribution, there is an equal 0.33, 0.33, 0.33 probability of sampling a singleton goal-reaching reward function, a random linear reward functions or a random mlp reward function for each training trajectory.
3. **[0b794c64]** (weight=1) A FRE agent has been trained on the ExORL `cheetah` (RND) dataset using the FRE-all prior rewards distribution
4. **[11bd7539]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `walker` (RND) dataset using the FRE-all prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
5. **[20b53e62]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `walker` (RND) dataset using the FRE-all prior rewards distribution, there is an equal 0.33, 0.33, 0.33 probability of sampling a singleton goal-reaching reward function, a random linear reward functions or a random mlp reward function for each training trajectory.
6. **[9e20fc23]** (weight=1) A FRE agent has been trained on the ExORL `walker` (RND) dataset using the FRE-all prior rewards distribution
7. **[355ad887]** (weight=1) The `exorl-cheetah-velocity` evaluation task has been implemented such that the agent is evaluated on the 4 reward functions outlined in addendum.md
8. **[152a0cb1]** (weight=1) The `exorl-cheetah-velocity` evaluation task has been implemented such that the average cumulative reward across the 4 reward functions is used as the evaluation metric
9. **[f8a8ff9c]** (weight=1) The `exorl-walker-velocity` evaluation task has been implemented such that the agent is evaluated on the 4 reward functions outlined in addendum.md
10. **[74f98f7f]** (weight=1) The `exorl-walker-velocity` evaluation task has been implemented such that the average cumulative reward across the 4 reward functions is used as the evaluation metric
11. **[484d1b87]** (weight=1) The `exorl-cheetah-goals` evaluation task has been implemented such that the agent is evaluated on the 5 reward functions outlined in addendum.md
12. **[8eceb966]** (weight=1) The `exorl-walker-goals` evaluation task has been implemented such that the agent is evaluated on the 5 reward functions outlined in addendum.md
13. **[2392fdea]** (weight=1) Code has been implemented such that a FRE agent trained on the `cheetah` (RND) dataset with the prior reward distribution referred to as FRE-all can been evaluated on `exorl-cheetah-velocity`
14. **[25b99cdd]** (weight=1) Code has been implemented such that a FRE agent trained on the `walker` (RND) dataset with the prior reward distribution referred to as FRE-all can been evaluated on `exorl-walker-velocity`

### Subtask 10 of 10: Reproduce the domain knowledge augmentation experiment (FRE-hint). Train FRE-hint agents on antmaze-large-diverse-v2 (using directional/XY-based augmented prior), on ExORL cheetah (using velocity-based augmented prior), and on ExORL walker (using velocity-based augmented prior). Evaluate FRE-hint on ant-directional, exorl-cheetah-velocity, and exorl-walker-velocity tasks. Compare FRE-hint performance to FRE-all on the same tasks and verify FRE-hint outperforms FRE-all on tasks matching the augmented prior. [hard]

**Success criteria:**

1. **[6c4fce0f]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-hint prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
2. **[b0d6d6b4]** (weight=1) Code has been implemented such that when training a FRE agent on the Ant MazE `antmaze-large-diverse-v2` dataset using the FRE-hint prior rewards distribution, the prior rewards distribution consists of all rewards corresponding to movement in a unit (x,y) direction.
3. **[6a19acfd]** (weight=1) A FRE agent has been trained on the Ant Maze `antmaze-large-diverse-v2` dataset using the FRE-hint prior rewards distribution
4. **[631eca30]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `cheetah` (RND) dataset using the FRE-hint prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
5. **[390a671a]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `cheetah` (RND) dataset using the FRE-hint prior rewards distribution, the prior rewards distribution consists of random initializations of reward functions rewarding the agent for moving in particular directions at particular speeds, forming a superset over the `exorl-cheetah-velocity` evaluation task.
6. **[a2b00b9a]** (weight=1) A FRE agent has been trained on the ExORL `cheetah` (RND) dataset using the FRE-hint prior rewards distribution
7. **[77f406ad]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `walker` (RND) dataset using the FRE-hint prior rewards distribution, the training and architecture hyperparameters specified in Appendix A are used.
8. **[ff48b670]** (weight=1) Code has been implemented such that when training a FRE agent on the ExORL `walker` (RND) dataset using the FRE-hint prior rewards distribution, the prior rewards distribution consists of random initializations of reward functions rewarding the agent for moving in particular directions at particular speeds, forming a superset over the `exorl-walker-velocity` evaluation task.
9. **[39866a97]** (weight=1) A FRE agent has been trained on the ExORL `walker` (RND) dataset using the FRE-hint prior rewards distribution
10. **[474b4b95]** (weight=1) Code has been implemented such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-hint can been evaluated on `ant-directional`
11. **[19d94a96]** (weight=1) Code has been executed such that a FRE agent trained on `antmaze-large-diverse-v2` with the prior reward distribution referred to as FRE-hint has been evaluated over 5 seeds with 20 episodes per seed on `ant-directional`.
12. **[62aa743f]** (weight=1) Code has been implemented such that a FRE agent trained on the `cheetah` (RND) dataset with the prior reward distribution referred to as FRE-hint can been evaluated on `exorl-cheetah-velocity`
13. **[076e55aa]** (weight=1) Code has been executed such that a FRE agent trained on the `cheetah` (RND) dataset with the prior reward distribution referred to as FRE-hint has been evaluated over 5 seeds with 20 episodes per seed on `exorl-cheetah-velocity`.
14. **[0431ce4a]** (weight=1) Code has been implemented such that a FRE agent trained on the `walker` (RND) dataset with the prior reward distribution referred to as FRE-hint can been evaluated on `exorl-walker-velocity`
15. **[ecf0ca0d]** (weight=1) Code has been executed such that a FRE agent trained on the `walker` (RND) dataset with the prior reward distribution referred to as FRE-hint has been evaluated over 5 seeds with 20 episodes per seed on `exorl-walker-velocity`.

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/fre_ara_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: fre

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
