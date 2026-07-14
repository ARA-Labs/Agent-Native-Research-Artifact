# Full Paper Reproduction: sequential-neural-score-estimation

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sequential-neural-score-estimation_ara_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sequential-neural-score-estimation_ara_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the paper's **structured research artifact (ARA)**. You have NO access to the original paper PDF or its companion GitHub repository.

**ARA artifact location**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/artifacts/sequential-neural-score-estimation`

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

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sequential-neural-score-estimation_ara_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Set up all 9 simulation tasks used in the paper: the 8 standard SBI benchmark tasks from the sbibm library (Gaussian Linear, Gaussian Mixture, Two Moons, Gaussian Linear Uniform, Bernoulli GLM, SLCP, SIR, Lotka Volterra) and the 31-parameter Pyloric neuroscience simulator (Cancer Borealis stomatogastric ganglion producing 18 summary statistics). For each task, verify that parameters can be sampled from the prior and observations generated from the simulator. Confirm correct dimensionality of parameters and observations for each task. [easy]

**Success criteria:**

1. **[18fa145c]** (weight=1) The Gaussian Linear task is available such that synthetic data can be sampled from the task
2. **[3a845c86]** (weight=1) The Gaussian Mixture task is available such that synthetic data can be sampled from the task
3. **[b0e7463b]** (weight=1) The Two Moons task is available such that synthetic data can be sampled from the task
4. **[636b493d]** (weight=1) The Gaussian Linear Uniform task is available such that synthetic data can be sampled from the task
5. **[8ffe1960]** (weight=1) The Bernoulli GLM task is available such that synthetic data can be sampled from the task
6. **[f6f6e39c]** (weight=1) The SLCP task is available such that synthetic data can be sampled from the task
7. **[584fceff]** (weight=1) The SIR task is available such that synthetic data can be sampled from the task
8. **[b84bf196]** (weight=1) The Lotka Volterra task is available such that synthetic data can be sampled from the task
9. **[33a68532]** (weight=1) The Neuroscience problem is available such that synthetic data can be sampled from the task

### Subtask 2 of 10: Implement the Variance-Exploding SDE (VESDE) forward noising process following Section 2.2 and Appendix E.3. Implement the VESDE drift term f(x,t)=0 and diffusion term g(t)=sigma_min*(sigma_max/sigma_min)^t*sqrt(2*log(sigma_max/sigma_min)). Set sigma_min=0.01 for SIR and Two Moons, sigma_min=0.05 for the remaining 6 benchmark tasks, and sigma_max to the maximum pairwise Euclidean distance in the training data (first-round data for sequential methods). Use time interval (0,1]. Implement code to compute the VESDE transition log-density gradients. Verify the forward process correctly adds increasing noise on at least two benchmark tasks. [easy]

**Success criteria:**

1. **[7cc9e28d]** (weight=1) The forward noising process has been implemented following Section 2.2
2. **[5cbe0a62]** (weight=1) The drift term for VESDE is defined as $f(x, t)=0$
3. **[d6a4a408]** (weight=1) The diffusion term for VESDE is defined as $g(t)=\sigma_{min} \cdot (\frac{\sigma_{min}}{\sigma_{max}})^t \cdot \sqrt{2 \log \frac{\sigma_{max}}{\sigma_{min}}}$
4. **[0d28b6c7]** (weight=1) The constant $\sigma_{\text{min}}$ for VESDE is set to 0.01 for the tasks SIR and Two Moons
5. **[394139bd]** (weight=1) The constant $\sigma_{\text{min}}$ for VESDE is set to 0.05 for the tasks Gaussian Linear, Gaussian Mixture, Gaussian Linear Uniform, Bernoulli GLM, SLCP, and Lotka Volterra
6. **[47bbd386]** (weight=1) The constant $\sigma_{\text{max}}$ for VESDE is chosen to be as large as the maximum Euclidean distance between all pairs of training data points for the current task. For sequential methods, the training data points that are used are the training data points available in the first round
7. **[ee6fc1b6]** (weight=1) The time interval used in VESDE is (0, 1]
8. **[7a91c729]** (weight=1) Code has been implemented for VESDE to compute the (gradients of the) transition log density

### Subtask 3 of 10: Implement the Variance-Preserving SDE (VPSDE) forward noising process following Appendix E.3. Implement the VPSDE drift term f(x,t)=-0.5*beta_t*theta_t where beta_t=beta_min+t*(beta_max-beta_min), and diffusion term g(t)=sqrt(beta_t). Set beta_min=0.1 and beta_max=11.0, time interval (0,1]. Implement code to compute the VPSDE transition log-density gradients. Verify the forward process correctly perturbs samples and that the marginal distribution at t=1 approximates a unit Gaussian. [easy]

**Success criteria:**

1. **[13d28eb6]** (weight=1) The drift term for VPSDE is defined as $f(x, t)=-\frac{1}{2}\beta_t\theta_t$, where $\beta_t = \beta_{\text{min}} + t(\beta_{\text{max}} - \beta_{\text{min}})$
2. **[da121c46]** (weight=1) The diffusion term for VPSDE is defined as $\sqrt{\beta_t}$, where $\beta_t = \beta_{\text{min}} + t(\beta_{\text{max}} - \beta_{\text{min}})$
3. **[c4621fe1]** (weight=1) The constant $\beta_\text{min}$ for VPSDE is set to 0.1
4. **[17102a8e]** (weight=1) The constant $\beta_\text{max}$ for VPSDE is set to 11.0
5. **[6a5e82b9]** (weight=1) The time interval used in VPSDE is (0, 1]
6. **[648352ef]** (weight=1) Code has been implemented for VPSDE to compute the (gradients of the) transition log density

### Subtask 4 of 10: Implement the three baseline methods and the C2ST evaluation metric. Set up Neural Posterior Estimation (NPE) using the sbibm library with training code. Set up Sequential Neural Posterior Estimation (SNPE-C) using the sbibm library with training code. Implement Truncated Sequential Neural Posterior Estimation (TSNPE) using the tsnpe_neurips GitHub repository. Implement the C2ST metric using the default sbibm implementation with 10000 samples from both the true and approximate posteriors. Configure the batch size to 200 for sequential experiments with budget <=10k. Verify that all three baselines can be trained and evaluated on at least one benchmark task. [easy]

**Success criteria:**

1. **[3a389c28]** (weight=1) The sbibm library is used to implement Neural Posterior Estimation (NPE)
2. **[4c097da3]** (weight=1) Code is implemented to train Neural Posterior Estimation (NPE) using the sbibm library
3. **[4c1cc604]** (weight=1) The sbibm library is used to implement Sequential Neural Posterior Estimation (SNPE)
4. **[e73d1064]** (weight=1) Code is implemented to train Sequential Neural Posterior Estimation (SNPE) using the sbibm library
5. **[02b42ffb]** (weight=1) Truncated Sequential Neural Posterior Estimation (TSNPE) is implemented using the GitHub repo https://github.com/mackelab/tsnpe_neurips
6. **[e7b8bc58]** (weight=1) C2ST has been implemented using the default implementation from `sbibm`, using default hyperparameters
7. **[ac2ef197]** (weight=1) When computing the C2ST score, 10000 samples from both the true posterior and the approximate posterior are used
8. **[dc9bd609]** (weight=1) For experiments with a simulation budget of either 1000 or 10000, the batch size is 200 for sequential experiments (TSNPSE-VE, TSNPSE-VP, SNPE, TSNPE)

### Subtask 5 of 10: Implement the conditional score network architecture exactly as specified in Appendix E.3. Build: (1) the parameter embedding network, a 3-layer MLP with 256 hidden units per layer and output dimension max(30, 4*d); (2) the observation embedding network, a 3-layer MLP with 256 hidden units per layer and output dimension max(30, 4*p); (3) the sinusoidal time embedding into 64 dimensions using sin(t/10000^((i-1)/31)) for i<=32 and cos(t/10000^((i-33)/31)) for i>32; (4) the score network MLP, a 3-layer MLP with 256 hidden units taking concatenated [theta_emb, x_emb, t_emb] with standardization of embeddings, outputting dimension d. All MLPs use SiLU activations. Verify correct output shapes for multiple benchmark tasks. [medium]

**Success criteria:**

1. **[97d46d53]** (weight=2) The parameter embedding network $\theta_t$ is a 3-layer fully-connected MLP with 256 hidden units in each layer.
2. **[3dcddd21]** (weight=1) The output dimension from the final layer of the parameter embedding network is determined by $\max (30, 4 \cdot d)$, where $d$ is the input dimension to the parameter embedding network
3. **[6e0acedb]** (weight=2) The observation embedding network $\x$ is a 3-layer fully-connected MLP with 256 hidden units in each layer
4. **[a3351355]** (weight=1) The output dimension from the final layer of the observation embedding network is determined by $\max (30, 4 \cdot p)$, where $p$ is the input dimension to the observation embedding network
5. **[31a17217]** (weight=1) The sinusoidal embedding $t$ is embedded into 64 dimensions
6. **[f7eafffb]** (weight=1) The sinusoidal embedding $t$ is computed as follows: the $i$-th value is computed as $\sin \left( \frac{t}{10000^{(i-1)/31}} \right)$ if $i \leq 32$, otherwise it is computed as $\cos \left( \frac{t}{10000^{((i-32)-1)/31}} \right)$
7. **[91963fec]** (weight=2) The score network is a 3-layer fully-connected MLP with 256 hidden units in each layer
8. **[cd67e43e]** (weight=2) Both the output of the parameter embedding network $\theta_t$ and output of the observation embedding network $x$ are standardized before being inputted to the score network, by subtracting an estimate of the mean and dividing by the standard deviation in each dimension. The empirical mean and empirical standard deviation of the training data is used
9. **[0203c1b6]** (weight=2) The score network takes the concatenated input $[\theta_{\text{emb}}, x_{\text{emb}}, t_{\text{emb}}] $, i.e. the outputs of the parameter embedding network, the output of the observation embedding network, and the output of the sinusoidal embedding network concatenated together
10. **[20d5ed76]** (weight=1) The output dimension of the score network is equal to the dimension of the parameter embedding network
11. **[50b24eb8]** (weight=1) All MLP networks use SiLU activation functions between layers

### Subtask 6 of 10: Implement the NPSE training and sampling pipeline. For training: (1) sample parameters from the prior and generate observations via the simulator; (2) simulate the forward diffusion to obtain perturbed parameters theta_t; (3) compute the denoising score matching loss as a Monte Carlo estimate. Configure the Adam optimizer with lr=1e-4, 15% validation split, early stopping with 1000-step patience, max 3000 iterations, batch size 50 for non-sequential experiments with budget <=10k, batch size 500 for budget 100k. For sampling: draw initial samples from unit Gaussian, solve the reverse-time probability flow ODE using RK45. Verify the training loop converges and posterior samples are generated on the Two Moons task. [medium]

**Success criteria:**

1. **[74bb4c17]** (weight=1) When training NPSE, for each sampled parameter from the prior $\theta_0$, code is implemented to use the simulator to generate a corresponding observation $x$; $x \sim p(x|theta_0)$
2. **[2dc54398]** (weight=1) When training NPSE, for each $\theta_0$ and corresponding observation $x$, code is implemented to simulate the forward diffusion process using an SDE to obtain $\theta_t$ at time $t$
3. **[da18282b]** (weight=2) When training NPSE, code is implemented to compute the loss as a Monte Carlo estimate of $\left\| s_\psi(\theta_t, x, t) - \nabla_{\theta_t} \log p_t(\theta_t | \theta) \right\|^2$, where $s_\psi(\theta_t, x, t)$ is the result of the score network, and $\nabla_{\theta_t} \log p_{t \mid 0}(\theta_t \mid \theta_0)$ is the forward diffusion transition log density
4. **[3b1bf848]** (weight=1) When sampling using NPSE, samples are drawn from the stationary distribution $\pi$ (unit gaussian distribution); $\overline{\theta}_0 \sim \pi(\cdot)$
5. **[eb61bf5c]** (weight=3) When sampling using NPSE, the approximation of the time-reversal of the probability flow ODE is implemented given some observation $x = x_{\text{obs}}$, and replacing the score of the (perturbed) posterior(s) with the neural network; $\nabla_\theta \log p_t(\theta \vert x_{\text{obs}}) \approx s_\psi(\theta_t, x_{\text{obs}}, t)$. RK45 is used to solve the ODE
6. **[c1c7b1ce]** (weight=1) Adam is used as the optimizer to train all networks
7. **[e32788d4]** (weight=1) A learning rate of 10^-4 is used when training all networks
8. **[6113057c]** (weight=1) 15% of each dataset is held out as a validation split. In sequential experiments, the validation split is re-computed on every round as 15% of the available simulations sampled uniformly at random
9. **[3a7eaa80]** (weight=1) After each training step the loss on the validation split is computed. If this validation loss doesn't decrease for 1000 steps, then training is stopped and the network that gave the lowest validation loss is returned
10. **[46eb9ccc]** (weight=1) The maximum number of training iterations is 3000
11. **[b69e449f]** (weight=1) For experiments with a simulation budget of either 1000 or 10000, the batch size is 50 for non-sequential experiments (NPSE-VE, NPSE-VP, NPE)
12. **[7f97ba49]** (weight=1) For simulation budgets of 100000 the batch size is 500 for all tasks

### Subtask 7 of 10: Train and evaluate all non-sequential methods (NPSE-VE, NPSE-VP, NPE) on all 8 benchmark tasks at simulation budgets 1000, 10000, and 100000, reproducing Figure 2 from Section 5.2. Evaluate using C2ST with 10000 samples. Verify per-task patterns: (1) Lotka Volterra: all three methods within +-0.15 C2ST; (2) SLCP: NPSE-VE and NPSE-VP roughly equivalent, both lower than NPE; (3) Gaussian Linear Uniform: NPE lower than both NPSE variants; (4) Bernoulli GLM: all roughly equivalent; (5) SIR: NPE lower than NPSE-VP; (6) Two Moons: NPE lower than NPSE-VP; (7) Gaussian Mixture: NPE and NPSE-VE roughly equivalent, both lower than NPSE-VP; (8) Gaussian Linear: all roughly equivalent. [medium]

**Success criteria:**

1. **[d221f378]** (weight=1) For each simulation budget 10^3, 10^4, 10^5, all non-sequential methods (NPSE-VE, NPSE-VP, NPE) have been trained on all tasks and evaluated using C2ST
2. **[c32110eb]** (weight=1) The recorded metrics show that, for the Lotka Volterra task, all methods NPSE-VE, NPSE-VP, and NPE achieve similar results to one-another (within +- 0.15 C2ST)
3. **[e5ea6fe2]** (weight=1) The recorded metrics show that, for the SLCP task, the methods NPSE-VE and NPSE-VP achieve roughly equivalent C2ST scores
4. **[089460fd]** (weight=1) The recorded metrics show that, for the SLCP task, the methods NPSE-VE and NPSE-VP both achieve lower C2ST scores than NPE
5. **[26b43594]** (weight=1) The recorded metrics show that, for the Gaussian Linear Uniform task, NPE achieves a lower C2ST score than both methods NPSE-VE and NPSE-VP
6. **[54cccd02]** (weight=1) The recorded metrics show that, for the Gaussian Linear Uniform task, the methods NPSE-VE and NPSE-VP achieve roughly equivalent C2ST scores
7. **[f4adb128]** (weight=1) The recorded metrics show that, for the Bernoulli GLM task, all methods NPSE-VE, NPSE-VP, and NPE achieve roughly equivalent C2ST scores
8. **[9a4dbff1]** (weight=1) The recorded metrics show that, for the SIR task, NPE achieves a lower C2ST score than NPSE-VP
9. **[b40d156e]** (weight=1) The recorded metrics show that, for the Two Moons task, NPE achieves a lower C2ST score than NPSE-VP
10. **[0e6a12ee]** (weight=1) The recorded metrics show that, for the Gaussian Mixture task, NPE and NPSE-VE achieve roughly equivalent C2ST scores
11. **[54e2553a]** (weight=1) The recorded metrics show that, for the Gaussian Mixture task, both NPE and NPSE-VE achieve lower C2ST scores than NPSE-VP
12. **[d560a5b0]** (weight=1) The recorded metrics show that, for the Gaussian Linear task, all methods NPSE-VE, NPSE-VP, and NPE achieve roughly equivalent C2ST scores

### Subtask 8 of 10: Implement the Truncated Sequential Neural Posterior Score Estimation (TSNPSE) algorithm following Section 4.1. The algorithm operates over R=10 rounds with budget evenly split (M=N/R per round). In round 1, the proposal prior equals the task prior. In subsequent rounds: (a) generate 20000 approximate posterior samples via the probability flow ODE; (b) compute sample log-probabilities using the instantaneous change-of-variables formula; (c) set the truncation boundary as the epsilon=5e-4 percentile; (d) implement truncated proposal sampling via rejection: draw from prior, reject outside the empirical hyperrectangle, compute log-probability, accept only if above threshold, repeat until M samples obtained. Each round, construct a new dataset from the truncated proposal and retrain the score network. Use the final-round score network for posterior sampling. Verify the algorithm runs for multiple rounds on at least one task. [hard]

**Success criteria:**

1. **[08b7d601]** (weight=1) In TSNPSE, given a total budget of $N$ simulations and $R$ rounds, the simulations are evenly distributed across rounds; the number of simulations per round $M$ is computed as $M=N/R$
2. **[48600e77]** (weight=1) In TSNPSE, the initial proposal prior is equivalent to the known prior of the current task; $p(\theta) =: p^{-0}(\theta)$
3. **[2fecc389]** (weight=1) In TSNPSE, in the $r$-th round, after applying the NPSE algorithm to learn a score network, 20000 samples are simulated from the approximate posterior via (the time-reversal of) the probability flow ODE using the neural network approximation of $\nabla_\theta \log p_t(\theta \vert x_{\text{obs}})$
4. **[34fde1e1]** (weight=1) In TSNPSE, in the $r$-th round, the (approximate) likelihood $p(\theta \mid x_{\text{obs}})$ of the samples under the model is computed using the instantaneous-change-of-variables formula
5. **[5a98077f]** (weight=1) In TSNPSE, in the $r$-th round, the truncation boundary is computed as the $\epsilon = 5 \times 10^{-4}$-th percentile of the samples from the approximate posterior. This defines the log-probability rejection threshold for rejection sampling.
6. **[dc661069]** (weight=1) In TSNPSE, in the $r$-th round, when sampling from the truncated proposal prior, samples are first drawn from the prior as $\theta \sim p(\theta)$.
7. **[c70a513b]** (weight=1) In TSNPSE, in the $r$-th round, when sampling from the truncated proposal prior, an initial rejection step is applied to samples drawn from the prior; the samples are rejected if they do not belong to the empirical hyperrectangle defined by the approximate posterior samples. That is, the hyperrectangle defined as the Cartesian product of the one-dimensional intervals with endpoints given by the minimum and maximum of the approximate posterior samples in each dimension.
8. **[c2e78e8a]** (weight=1) In TSNPSE, in the $r$-th round, when sampling from the truncated proposal prior, following the initial rejection step, the likelihood of the samples from the prior under the approximate posterior is computed using the instantaneous change-of-variables formula.
9. **[e17ca159]** (weight=1) In TSNPSE, in the $r$-th round, when sampling from the truncated proposal prior, samples are accepted if the likelihood under the approximation posterior is greater than the truncation boundary that has been computed on the $r$-th round. Otherwise they are rejected.
10. **[eb56d7bc]** (weight=1) In TSNPSE, in the $r$-th round, when sampling from the truncated proposal prior, the previous steps are repeated until the required number of samples from the proposal prior have been obtained.
11. **[6cf7e83a]** (weight=3) In TSNPSE, in the $r$-th round, a dataset $\mathcal{D}$ of $|M|$ samples is constructed by drawing $\theta_i \sim {p}^{-r-1}(\theta)$, $x_i \sim p(x \mid \theta_i)$, and adding $(\theta_i, x_i)$ to $\mathcal{D}$, where ${p}^{-r-1}(\theta)$ denotes the proposal prior and $p(x|\theta)$ denotes the simulator.
12. **[d2f135a0]** (weight=3) In TSNPSE, in each of the rounds, given a dataset $\mathcal{D}$ of $|M|$ samples, the NPSE algorithm is followed to learn a neural network which approximates the score(s) of the perturbed posterior(s) $\nabla_{\theta_t} \log p_t(\theta_t | x)$
13. **[2d2d46c3]** (weight=3) In TSNPSE, the score network computed in the final round is used as the final approximation of the scores $\nabla_{\theta_t} \log p_t(\theta_t | x)$, and can be used to generate approximate samples from the posterior, as per the standard NPSE algorithm

### Subtask 9 of 10: Train and evaluate all sequential methods (TSNPSE-VE, TSNPSE-VP, SNPE-C, TSNPE) for 10 rounds on all 8 benchmark tasks at simulation budgets 10000 and 100000, reproducing Figure 3 from Section 5.2. Evaluate using C2ST. Verify: (1) on SLCP, Lotka Volterra, and Bernoulli GLM, TSNPSE-VE and TSNPSE-VP achieve lower or roughly equivalent C2ST compared to SNPE-C and TSNPE; (2) on Gaussian Linear, TSNPSE variants achieve lower or equivalent C2ST compared to TSNPE; (3) on simpler tasks (GLU, Bernoulli GLM, SIR, Two Moons, Gaussian Mixture, Gaussian Linear), TSNPSE-VE and TSNPSE-VP achieve equivalent or higher C2ST compared to SNPE-C; (4) on GLU, SIR, Two Moons, Gaussian Mixture, TSNPSE-VE achieves equivalent or higher C2ST compared to TSNPE; (5) on GLU, Bernoulli GLM, SIR, Two Moons, Gaussian Mixture, Gaussian Linear, TSNPSE-VP achieves equivalent or higher C2ST compared to TSNPE. [hard]

**Success criteria:**

1. **[3edc4750]** (weight=3) For each simulation budget 10^3, 10^4, 10^5, all sequential methods (TSNPSE-VE, TSNPSE-VP, SNPE, TSNPE) have been trained for 10 rounds on all tasks and evaluated using C2ST
2. **[4f22134a]** (weight=1) The recorded metrics show that, for the tasks SLCP, Lotka Volterra, and Bernoulli GLM, TSNPSE-VE and TSNPSE-VP achieves a lower or roughly equivalent C2ST score than both SNPE and TSNPE
3. **[9176d64d]** (weight=1) The recorded metrics show that, for the Gaussian Linear task, TSNPSE-VE and TSNPSE-VP achieve a lower or roughly equivalent C2ST score compared to TSNPE
4. **[5cb794a0]** (weight=1) The recorded metrics show that, for the tasks Gaussian Linear Uniform, Bernoulli GLM, SIR, Two Moons, Gaussian Mixture, and Gaussian Linear, TSNPSE-VE achieves an equivalent or higher C2ST score compared to SNPE
5. **[e4090d0e]** (weight=1) The recorded metrics show that, for the tasks Gaussian Linear Uniform, Bernoulli GLM, SIR, Two Moons, Gaussian Mixture, and Gaussian Linear, TSNPSE-VP achieves an equivalent or higher C2ST score compared to SNPE
6. **[4da588d3]** (weight=1) The recorded metrics show that, for the tasks Gaussian Linear Uniform, SIR, Two Moons, and Gaussian Mixture, TSNPSE-VE achieves an equivalent or higher C2ST score compared to TSNPE
7. **[1e34fed1]** (weight=1) The recorded metrics show that, for the tasks Gaussian Linear Uniform, Bernoulli GLM, SIR, Two Moons, Gaussian Mixture, and Gaussian Linear, TSNPSE-VP achieves an equivalent or higher C2ST score compared to TSNPE

### Subtask 10 of 10: Reproduce the Pyloric neuroscience experiment from Section 5.3 (Figures 4a-c). Run TSNPSE-VP for 9 rounds: 30000 initial simulations from the prior, then 20000 additional simulations per round from the truncated proposal. After each round, compute the percentage of valid summary statistics (non-NaN outputs from the Pyloric simulator). At the end of the final round, compute a posterior mean-predictive sample by taking the mean of approximate posterior samples and running it through the simulator. Verify: (1) TSNPSE-VP achieves approximately [X]% valid summary statistics in the final round; (2) TSNPSE-VP has a higher percentage of valid statistics than TSNPE and SNVI for all simulation budgets below 200k; (3) the posterior predictive samples closely match the experimentally observed voltage traces. [hard]

**Success criteria:**

1. **[1512d34f]** (weight=1) SNPSE-VP is trained with inference over 9 rounds, with 30000 initial simulations and 20000 added simulations in each round
2. **[db05a3d3]** (weight=1) The percentage of valid summary statistics from each method is computed after each round, where an invalid summary statistic is when the Pyloric simulator returns a `NaN` (in one or more of the output dimensions)
3. **[13c6dc3c]** (weight=1) A posterior mean-predictive sample is computed at the end of the final round, by first computing the mean of the approximate posterior samples, then acquiring a simulation
4. **[46447a4d]** (weight=1) The recorded metrics show that, in the final round, SNPSE-VP achieves about [X]% valid summary statistics
5. **[3fb824b3]** (weight=1) The recorded metrics show that SNPSE-VP has a higher percentage of valid summary statistics for all simulation budgets less than 200*10^3 compared to TSNPE and SNVI
6. **[445ce9cf]** (weight=1) The recorded metrics for the results in Section 5.3 show that, the obtained posterior produces samples which closely match the observed data

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sequential-neural-score-estimation_ara_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: sequential-neural-score-estimation

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
