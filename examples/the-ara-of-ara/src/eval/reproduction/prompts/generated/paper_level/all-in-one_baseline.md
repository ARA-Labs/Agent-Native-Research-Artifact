# Full Paper Reproduction: all-in-one

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/all-in-one_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/all-in-one_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/all-in-one.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/all-in-one` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/all-in-one_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the Variance Exploding SDE (VESDE) with drift f(x,t)=0, diffusion g(t), and perturbation kernel using sigma_max=15, sigma_min=0.0001, and time interval [1e-5,1]. Implement the Simformer tokenizer that maps (identifier, value, metadata, condition-state) tuples into token embeddings using learnable identifier embeddings, scalar-repeat value embeddings, random Fourier metadata embeddings, and learned condition-state embeddings. Verify on a simple distribution that the SDE and tokenizer produce valid outputs. [easy]

**Success criteria:**

1. **[0ac16f05]** (weight=2) The drift term for Variance Exploding SDE is defined as $f(x, t)=0$
2. **[1402caf0]** (weight=2) The diffusion term for Variance Exploding SDE is defined as $g(t)=\sigma_{min} \cdot (\frac{\sigma_{max}}{\sigma_{min}})^t \cdot \sqrt{2 \log \frac{\sigma_{max}}{\sigma_{min}}}$
3. **[396c0b27]** (weight=2) The perturbation kernel for the Variance Exploding SDE is defined as $p(x_t|x_0) = \mathcal{N}(x_t, x_t, \sigma(t)I)$ where $\sigma(t) = \sigma_{min}^2\left( \frac{\sigma_{max}}{\sigma_{min}} \right)^{2t}$
4. **[07f7aac1]** (weight=1) The constant $\sigma_{max}$ for VESDE is set to 15
5. **[c6cd56ae]** (weight=1) The constant $\sigma_{min}$ for VESDE is set to 0.0001
6. **[ac3759f1]** (weight=1) In VESDE, samples are drawn from the time interval [1e-5, 1]
7. **[437abe9f]** (weight=1) Each unique variable has an integer identifier. Multiple observations of the same variable share the same identifier
8. **[714bdd7e]** (weight=1) The tokenizer uses learnable vector embeddings to embed each identifier
9. **[af5cd308]** (weight=1) The embedding for a single value is created by repeating the scalar value to match the desired dimensionality. For example, to embed the value 1 to desired dimensionality N, we would have a vector [1, 1, ...., 1] of length N
10. **[2e46fc8d]** (weight=1) The tokenizer correctly tokenizes and embeds the metadata (if required); the tokenizer applies a learnable linear mapping of a random Fourier embedding of the elements in the index set to the desired dimensionality.
11. **[2ff0a481]** (weight=1) The tokenizer uses learnable vector embeddings to embed each value in a condition state - "True" values are mapped to a shared learnable vector embedding, whereas "False" values are mapped to zeros (of the desired dimensionality)
12. **[407dcc3b]** (weight=1) For each input, the tokenizer concatenates the embeddings of the identifier, value, metadata (if used), and condition state in that order
13. **[c6eb15a5]** (weight=1) The tokenizer takes inputs: a sequence of scalar values, a sequence of integer variable identifiers, a condition mask $M_C$, and optional metadata if required. It embeds these inputs into a sequence of tokens, each of equal dimensionality

### Subtask 2 of 10: Implement the Simformer transformer architecture with masked self-attention, single linear decoder producing per-token scalar scores, and diffusion-time conditioning via random Fourier features added after each feed-forward block. Implement the condition mask M_C sampling (joint, posterior, likelihood, Bernoulli p=0.3/0.7) and three attention mask variants (dense, undirected-graph, directed-graph with Webb et al. edge-addition algorithm). Implement the masked denoising score-matching loss with weighting lambda(t)=g(t)^2 applied only to unobserved variables. Implement the Euler-Maruyama reverse-SDE sampler where the reverse process runs on unobserved variables while observed variables are held constant. Verify mask shapes, loss computation, and sampling on synthetic data. [easy]

**Success criteria:**

1. **[09008e24]** (weight=2) The Simformer model is a slightly modified vanilla encoder-only transformer following the implementation proposed by (Vaswani et al., 2017). The only modification is that the decoder is a single linear layer that produces a single scalar score for each variable token in the input sequence. The Simformer model is described in Section 3, Figure 2, and Appendix A.1
2. **[b1b80f04]** (weight=1) Diffusion time is embedded as a random Gaussian Fourier embedding, and a linear projection of diffusion time is added to the output of each feed-forward block in the transformer
3. **[25eecc1a]** (weight=1) The Simformer takes inputs: the diffusion time $t$, a sequence of tokens from the tokenizer, and an attention mask. These are projected to a sequence of scalar outputs, representing the marginal scores of the diffusion process at time $t$.
4. **[be65afa3]** (weight=1) During training, for each training sample, the condition mask $M_C$ is randomly sampled as either 1) the joint distribution, where $M_C=[0, 0, ..., 0]$, 2) the posterior distribution where data variables are observed and parameters are unobserved, 3) the likelihood function where data variables are unobserved and parameter variables are observed, 4) a Bernoulli distribution with p=0.3 (resampled for each element), 5) a Bernoulli distribution with p=0.7 (resampled for each element)
5. **[3e515973]** (weight=1) $M_E$ is selected to be undirected, directed, or fully dense
6. **[8e07cc4f]** (weight=1) If $M_E$ is selected to be fully dense, every token is allowed to attend to every other token
7. **[08a90ef1]** (weight=1) For both undirected and directed cases, the attention mask $M_E$ is computed to capture the known dependencies of the current task. Specifically, each task provides $M_E$ as given by the adjacency matrix of a directed/undirected graphical model with the diagonal set to True.
8. **[6f05f0cf]** (weight=1) If $M_E$ is directed it must be updated for a given $M_C$. The algorithm proposed by Webb at al. (2018) is used to add the minimal number of edges required to represent additional dependencies from conditioning as specified in $M_C$
9. **[34b6fc70]** (weight=1) When training the Simformer, for each training sample $\hat{x}_0$, the noise level $t$ is sampled in the range [1e-5, 1] to generate a (partially) noisy sample $\hat{\mathbf{x}}_t^{M_C} = (1 - M_C) \cdot \hat{\mathbf{x}}_t + M_C \cdot \hat{\mathbf{x}}_0$ i.e. variables that we want to condition on remain clean.
10. **[0e335268]** (weight=1) A diffusion model loss is used that targets (un)conditional marginal score $\nabla_{\mathbf{x}_t^{\text{unobserved}}}\,\log p_t(\mathbf{x}_t^{\text{unobserved}} \mid \mathbf{x}^{\text{observed}})$ as defined by the condition mask $M_C$ and p(x).
11. **[b3e915ef]** (weight=1) As defined in Section 3.3, for each (partially) noisy training sample $\hat{x}_t^{M_c}$, the Simformer loss is defined as: $\ell(\phi, M_C, t, \hat{\mathbf{x}}_0, \hat{\mathbf{x}}_t) = (1-M_C)\cdot \left(s_\phi^{M_E}(\hat{\mathbf{x}}_t^{M_C}, t) - \nabla_{\hat{\mathbf{x}}_t} \log p_t(\hat{\mathbf{x}}_t|\hat{\mathbf{x}}_0)\right)$, where $s_\phi^{M_E}$ denotes the score model equipped with a specific attention mask $M_E$
12. **[e3cd228e]** (weight=1) The Simformer loss is only computed over samples that are unobserved, i.e., they have a value of 0 in $M_C$
13. **[2cb4d86f]** (weight=1) The total Simformer loss per mini-match is given by a weighted sum, as given by a positive weighting function $\lambda(t)$ e.g. $\lambda(t)=g(t)^2$ where $g(t)$ is the diffusion coefficient of the VESDE.
14. **[79df6718]** (weight=1) When performing inference using Simformer, the reverse diffusion process is run on all unobserved variables. Observed variables are kept constant at their initial values
15. **[7c953e3a]** (weight=1) Euler-Maruyama discretization has been implemented to run the diffusion process backward for Simformer

### Subtask 3 of 10: Implement baselines and evaluation infrastructure. Implement NPE, NRE, and NLE via the sbi library with neural spline flows, batch size 1000, Adam optimizer, and early stopping. Implement C2ST evaluation using a random forest classifier with 100 trees and 5-fold cross-validation. Set up the 500-step Euler-Maruyama discretization for Simformer sampling. Prepare the four SBIBM benchmark tasks (Gaussian Linear, Gaussian Mixture, Two Moons, SLCP) with their MCMC reference samplers: Two Moons uses 1000 slice-sampling steps + 3000 MHMCMC steps (step size 0.01); SLCP uses 600 slice steps. Generate >=1000 reference samples per task. [easy]

**Success criteria:**

1. **[23d6d4c9]** (weight=1) 500 steps are used in the Euler-Maruyama discretization process for Simformer
2. **[ad5f1aac]** (weight=2) The sbi library (Tejero-Cantero et al., 2020) is used to implement NPE, NRE, and NLE. Default parameters from the library are used, aside from using a more expressive neural spine flow for NPE and NLE
3. **[ee41ea7c]** (weight=1) Each method NPE, NRE, and NLE is trained using the provided training loop (e.g. sbi.SNPE().train())
4. **[31ed240f]** (weight=1) Each method NPE, NRE and NLE uses a batch size of 1000
5. **[6a1ddafa]** (weight=1) Each method NPE, NRE and NLE uses the Adam optimizer
6. **[56dcd071]** (weight=1) Early stopping is used to stop training early depending on validation loss
7. **[3957cfb9]** (weight=1) Given inputs X and Y, the classifier-based two-sample test accuracy between X and Y is measured as the 5-fold cross-validation score
8. **[982f7456]** (weight=1) The classifier is a random forest classifier with 100 trees
9. **[973db5a3]** (weight=1) A score of 0.5 signifies perfect alignment with the ground truth posterior, and 1.0 indicates that a classifier can completely distinguish between the approximation and the ground truth
10. **[23688299]** (weight=1) The tasks Gaussian Linear, Gaussian Mixture, Two Moons, and SLCP are available such that synthetic data can be sampled from each task
11. **[9fa888e9]** (weight=1) N Markov chains with samples are initialized from the joint distribuiton
12. **[ed3ab4fa]** (weight=1) 1000 steps of a random direction slice sampling algorithm are run
13. **[e4d0c4d5]** (weight=1) An additional 3000 steps of Metropolis-Hastings Markov Chain Monte Carlo (MHMCMC) are run with step size of 0.01
14. **[92486973]** (weight=1) Only the last samples of each chain are considered, yielding N reference samples
15. **[c09ac29b]** (weight=1) For each of the tasks Gaussian Linear, Gaussian Mixture, Two Moons, and SLCP, N >= 1000 reference samples are generated

### Subtask 4 of 10: Complete the SBIBM reference data preparation for SLCP (600 slice + 2000 MHMCMC steps, keep last sample per chain). Train NPE on all four SBIBM tasks (Linear Gaussian, Mixture Gaussian, Two Moons, SLCP) at simulation budgets 10^3, 10^4, 10^5. Obtain 10 ground-truth posteriors per task. Generate N posterior samples from each NPE model and compute C2ST scores to establish the NPE baseline for comparison with Simformer. [medium]

**Success criteria:**

1. **[af3a4299]** (weight=1) N Markov chains with samples are initialized from the joint distribuiton
2. **[028a6cbe]** (weight=1) 600 steps of a random direction slice sampling algorithm are run
3. **[1e941abb]** (weight=1) An additional 2000 steps of Metropolis-Hastings Markov Chain Monte Carlo (MHMCMC) are run with step size of 0.1
4. **[0051bf87]** (weight=1) Only the last samples of each chain are considered, yielding N reference samples
5. **[bc21d6d1]** (weight=1) For the Linear Gaussian task, NPE has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
6. **[174cb2a9]** (weight=1) For the Mixture Gaussian task, NPE has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
7. **[a5d7b1c2]** (weight=1) For the Two Moons task, NPE has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
8. **[f2ad95c5]** (weight=1) For the SLCP task, NPE has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
9. **[a4ad0e3d]** (weight=1) For the Linear Gaussian task, samples for ten ground-truth posteriors are obtained
10. **[2ac19789]** (weight=1) For the Mixture Gaussian task, samples for ten ground-truth posteriors are obtained
11. **[fd64cfd0]** (weight=1) For the Two Moons task, samples for ten ground-truth posteriors are obtained
12. **[8f6a3486]** (weight=1) For the SLCP task, samples for ten ground-truth posteriors are obtained
13. **[183cc3f0]** (weight=1) For the Linear Gaussian task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors and ground-truth posteriors have been calculated
14. **[6a97b353]** (weight=1) For the SLCP task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors and ground-truth posteriors have been calculated

### Subtask 5 of 10: Train three Simformer variants (dense, undirected-graph, directed-graph attention) with 6 layers, token dim 50, 4 heads, key/query/value dim 10, Fourier metadata embedding 128d, Fourier time embedding 256d, FF hidden dim 150, batch size 1000, Adam optimizer, VESDE, on all four SBIBM tasks (Linear Gaussian, Mixture Gaussian, Two Moons, SLCP) at simulation budgets 10^3, 10^4, 10^5. For each trained model, generate N posterior samples from 10 reference observations and compute C2ST. Verify that Simformer variants almost always outperform NPE and that structured attention significantly outperforms dense on Linear Gaussian and SLCP. [medium]

**Success criteria:**

1. **[cdf1bfdd]** (weight=1) All Simformers have a token dimension of 50
2. **[e9edc2a0]** (weight=1) All Simformers have 4 heads
3. **[32e4ef3f]** (weight=1) In all Simformers, the dimensionality of the key, query and value is 10
4. **[da87d682]** (weight=1) In all Simformers, the random Gaussian Fourier embedding used in the tokenizer to embed metadata objects has 128 dimensions (if required)
5. **[5963d717]** (weight=1) In all Simformers, the random Gaussian Fourier embedding used for diffusion time has 256 dimensions
6. **[85db9bf8]** (weight=1) In all Simformers, the feed-forward block expands to a hidden dimension of 150.
7. **[b18e9e5a]** (weight=1) In all Simformers, a batch size of 1000 is used
8. **[831ca2ca]** (weight=1) The Adam optimizer is used to train all Simformers
9. **[7ec03b27]** (weight=1) Variance Exploding SDE (VESDE) is used to train the Simformer in all experiments
10. **[237efc4f]** (weight=1) Simformers used for all experiments in Section 4.1 have 6 layers
11. **[71d1e184]** (weight=1) For the Linear Gaussian task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
12. **[3628b28c]** (weight=1) For the Linear Gaussian task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
13. **[8f4524fc]** (weight=1) For the Linear Gaussian task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
14. **[a7604584]** (weight=1) Across all four benchmark tasks (Linear Gaussian, Mixture Gaussian. Two Moons, SLCP) when approximating the posterior distribution, all Simformer variants almost always outperform neural posterior estimation (NPE) wrt. C2ST accuracy
15. **[1755440f]** (weight=1) When approximating the posterior distribution, both the Simformer with undirected graph and Simformer with directed graph significantly outperform the regular Simformer on the Linear Gaussian and SLCP tasks wrt. C2ST accuracy

### Subtask 6 of 10: Complete the posterior benchmark C2ST evaluation. Train Simformer variants (dense, undirected, directed) on Mixture Gaussian, Two Moons, and SLCP at budgets 10^3, 10^4, 10^5. Generate N posterior samples from each trained model and compute C2ST for all four SBIBM tasks (including Linear Gaussian from T05). Verify that the structured Simformer achieves approximately 10x simulation efficiency over NPE averaged across all benchmark tasks. [medium]

**Success criteria:**

1. **[20c740b8]** (weight=1) For the Mixture Gaussian task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
2. **[152f3333]** (weight=1) For the Mixture Gaussian task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
3. **[fabc5fd9]** (weight=1) For the Mixture Gaussian task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
4. **[d47f5e4e]** (weight=1) For the Two Moons task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
5. **[629c1323]** (weight=1) For the Two Moons task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
6. **[ec9c4b69]** (weight=1) For the Two Moons task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
7. **[3859bb58]** (weight=1) For the SLCP task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
8. **[fe86ca91]** (weight=1) For the SLCP task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
9. **[5bbb52eb]** (weight=1) For the SLCP task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
10. **[3a9eb157]** (weight=1) For the Linear Gaussian task, for each model trained for 10^3, 10^4, and 10^5 simulations, N posterior samples are generated from the 10 different reference observations, where N is the number of reference samples
11. **[157423ff]** (weight=1) For the Mixture Gaussian task, for each model trained for 10^3, 10^4, and 10^5 simulations, N posterior samples are generated from the 10 different reference observations, where N is the number of reference samples
12. **[56cf845a]** (weight=1) For the Two Moons task, for each model trained for 10^3, 10^4, and 10^5 simulations, N posterior samples are generated from the 10 different reference observations, where N is the number of reference samples
13. **[2270f417]** (weight=1) For the SLCP task, for each model trained for 10^3, 10^4, and 10^5 simulations, N posterior samples are generated from the 10 different reference observations, where N is the number of reference samples
14. **[59965170]** (weight=1) For the Mixture Gaussian task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors and ground-truth posteriors have been calculated
15. **[1149eae8]** (weight=1) For the Two Moons task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors and ground-truth posteriors have been calculated

### Subtask 7 of 10: Reproduce the arbitrary-conditional evaluation from Section 4.1 (Figure 4b). Prepare the Tree and HMM structured tasks with HMC-based reference sampling (5000 HMC steps per chain, N>=1000 samples). Train Simformer variants (dense, undirected, directed) with 6 layers at budgets 10^3, 10^4, 10^5 on Tree, HMM, Two Moons, and SLCP. For each task, generate MCMC ground-truth samples for 100 randomly selected conditionals, produce matching Simformer samples, compute C2ST for each conditional, and verify all models achieve mean C2ST below 0.7 at 10^5 simulations. [hard]

**Success criteria:**

1. **[1f652a29]** (weight=1) The Tree task is available such that synthetic data can be sampled
2. **[acc664bc]** (weight=1) N Markov chains with samples are initialized from the joint distribution
3. **[35e0a7bf]** (weight=1) 5000 steps of a HMC sampler is run
4. **[462ad866]** (weight=1) Only the last samples of each chain are considered, yielding N reference samples
5. **[36605b43]** (weight=1) For the Tree task, N >= 1000 reference samples are generated
6. **[6fc3436c]** (weight=1) The HMM task is available such that synthetic data can be sampled
7. **[52f952b5]** (weight=1) N Markov chains with samples are initialized from the joint distribution
8. **[293a5a7e]** (weight=1) 5000 steps of a HMC sampler is run
9. **[bc5f359e]** (weight=1) Only the last samples of each chain are considered, yielding N reference samples
10. **[321d7fd3]** (weight=1) For the HMM task, N >= 1000 reference samples are generated
11. **[ee48f977]** (weight=1) For the HMM task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
12. **[dbb902c0]** (weight=1) For the HMM task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
13. **[0ec528ea]** (weight=1) For the HMM task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
14. **[4a7698c5]** (weight=1) For the Tree task, Simformer (with a dense attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
15. **[5fdb707e]** (weight=1) For the Tree task, Simformer (with an undirected graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)

### Subtask 8 of 10: Complete the arbitrary-conditional C2ST evaluation for all four tasks (Tree, HMM, Two Moons, SLCP). Compute C2ST between model-generated and MCMC ground-truth samples for each task at all simulation budgets. Verify all Simformer models achieve C2ST below 0.7 at 10^5. Additionally reproduce the Lotka-Volterra experiment from Section 4.2: implement the predator-prey ODE simulator with Gaussian noise sigma=0.1, train an 8-layer dense-attention Simformer at 10^3/10^4/10^5, and verify C2ST<0.65 for posterior and C2ST<0.75 for arbitrary conditionals using the ~10x simulation-efficiency metric. [hard]

**Success criteria:**

1. **[5730c287]** (weight=1) For the Tree task, Simformer (with a directed graph for it's attention mask) has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
2. **[dd3a0c20]** (weight=1) For the Tree task, ground truth posterior samples with Markov-Chain Monte-Carlo are generated on 100 randomly sampled selected conditional or full joint distributions
3. **[82cb5063]** (weight=1) For the HMM task, ground truth posterior samples with Markov-Chain Monte-Carlo are generated on 100 randomly sampled selected conditional or full joint distributions
4. **[409deb4c]** (weight=1) For the Two Moons task, ground truth posterior samples with Markov-Chain Monte-Carlo are generated on 100 randomly sampled selected conditional or full joint distributions
5. **[c2239ebc]** (weight=1) For the SLCP task, ground truth posterior samples with Markov-Chain Monte-Carlo are generated on 100 randomly sampled selected conditional or full joint distributions
6. **[77fa71bf]** (weight=1) For the Tree task, for each model trained for 10^3, 10^4, and 10^5 simulations, for each of the ground truth posterior samples, N model-generated posteriors are created by conditioning on the observations, where N is the number of reference samples
7. **[913b099a]** (weight=1) For the HMM task, for each model trained for 10^3, 10^4, and 10^5 simulations, for each of the ground truth posterior samples, N model-generated posteriors are created by conditioning on the observations, where N is the number of reference samples
8. **[7413d98d]** (weight=1) For the Two Moons task, for each model trained for 10^3, 10^4, and 10^5 simulations, for each of the ground truth posterior samples, N model-generated posteriors are created by conditioning on the observations, where N is the number of reference samples
9. **[a2fe39cd]** (weight=1) For the SLCP task, for each model trained for 10^3, 10^4, and 10^5 simulations, for each of the ground truth posterior samples, N model-generated posteriors are created by conditioning on the observations, where N is the number of reference samples
10. **[c1fdd141]** (weight=1) For the Tree task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors (trained on 10^3, 10^4 and 10^5 simulations and conditioned on observations) and ground-truth posteriors have been calculated
11. **[0ece9e6e]** (weight=1) For the HMM task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors (trained on 10^3, 10^4 and 10^5 simulations and conditioned on observations) and ground-truth posteriors have been calculated
12. **[2a4fd54c]** (weight=1) For the Two Moons task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors (trained on 10^3, 10^4 and 10^5 simulations and conditioned on observations) and ground-truth posteriors have been calculated
13. **[99bb3116]** (weight=1) For the SLCP task, for each model trained for 10^3, 10^4, and 10^5 simulations, Classifier Two-Sample Test accuracy between the model-generated posteriors (trained on 10^3, 10^4 and 10^5 simulations and conditioned on observations) and ground-truth posteriors have been calculated
14. **[86499107]** (weight=1) When approximating the posterior distribution, averaged across all benchmark tasks (Linear Gaussian, Mixture Gaussian. Two Moons, SLCP) and number of simulations used in training, the Simformer required about 10 times fewer simulations than NPE to achieve similar performance wrt. C2ST accuracy
15. **[b858fec6]** (weight=3) When evaluating arbitrary conditionals on tasks Tree, HMM, Two Moons, and SLCP, when trained with 10^5 simulations, all Simformer models on all tasks achieve low C2ST (below 0.7)

### Subtask 9 of 10: Reproduce the Lotka-Volterra (Section 4.2) and SIRD (Section 4.3) application experiments. For Lotka-Volterra: implement the predator-prey ODE simulator with Gaussian noise (sigma=0.1) operating on the full time-series without summary statistics, train an 8-layer Simformer on 10^5 simulations, condition on 4 irregular prey observations to infer posterior and posterior predictives, then add 9 predator observations and verify that uncertainty decreases, ground-truth parameters lie within high-probability regions, and C2ST is below 0.65 for posterior and below 0.75 for arbitrary conditionals. [hard]

**Success criteria:**

1. **[9f70a4e5]** (weight=1) The Lotka Volterra task is available such that synthetic data can be sampled
2. **[bcf546a2]** (weight=1) For Lotka-Volterra, inference is performed for the full time-series and the implementation doesn't rely on summary statistics.
3. **[efe8edda]** (weight=1) In the Lotka Volterra task, to each simulation, Gaussian observation noise is added with $\sigma=0.1$
4. **[aa888ef9]** (weight=1) The Simformer used for all experiments in Section 4.2 has 8 layers
5. **[7ec881a6]** (weight=1) The Simformer in section 4.2 has been trained for 10^3, 10^4, and 10^5 simulations (in separate training runs)
6. **[f4bb304f]** (weight=1) Four synthetic prey observations are sampled at random times
7. **[1f9a15cb]** (weight=1) The Simformer trained on 10^5 simulations of Lotka-Volterra is used with a dense attention mask to infer the posterior distribution on a uniform grid between t=0 and t=15, given the four synthetic observations and posterior predictive samples for unobserved predator and prey variables.
8. **[2da3fc50]** (weight=2) The ground truth parameter is usually within regions of high posterior probability, using the Simformer with a dense attention mask trained on 10^5 simulations of Lotka-Volterra
9. **[6cae1579]** (weight=1) Nine additional synthetic observations of the predator population are sampled from Lotka-Volterra at random times
10. **[c31c4bfa]** (weight=1) The Simformer (trained on 10^5 simulations of Lotka-Volterra) with a dense attention mask is used to infer the posterior distribution given the four prey synthetic observations and nine predator synthetic observations
11. **[0f4a0b23]** (weight=2) Including the nine predator synthetic observations reduces the uncertainty in the posterior predictive of both prey and predator populations, when using the Simformer trained on 10^5 simulations of Lotka-Volterra
12. **[df75afbb]** (weight=2) Including the nine predator measurements reduces the uncertainty in both the posterior, when using the Simformer trained on 10^5 simulations of Lotka-Volterra
13. **[2551546a]** (weight=1) All Simformers trained on 10^3, 10^4, 10^5 simulations of Lotka-Volterra are separately used to sample from arbitrary conditional distributions to simultaneously generate posterior and posterior predictive samples
14. **[173a3eec]** (weight=2) Using the Simformer trained for 10^5 simulations of Lotka-Volterra, the C2ST performance (posterior distribution) is below 0.65
15. **[e87233c0]** (weight=2) Using the Simformer trained for 10^5 simulations of Lotka-Volterra, the C2ST performance (arbitrary conditionals) is below 0.75

### Subtask 10 of 10: Reproduce the SIRD (Section 4.3) and Hodgkin-Huxley (Section 4.4) experiments with guided diffusion for interval constraints (Algorithm 1). For SIRD: implement the epidemic simulator with time-varying contact rate beta(t) from GP+RBF+sigmoid, uniform gamma/delta prior [0,0.5], log-normal noise sigma=0.05, train 8-layer dense Simformer, verify parameter recovery and predictive fit for both scenarios (5 I/R/D observations; 4 beta + 1 death observation). For HH: implement the simulator with 7 parameters, V0=-65mV, 200ms, 4mA input 50-150ms, rate functions, voltage summaries, metabolic energy. Implement Algorithm 1 (self-recurrence r, c(x)=x-u, s(t)=1/sigma^2). Train 8-layer dense Simformer. Verify unconstrained posterior and apply energy-interval constraint (lowest [X]% quantile) via guided diffusion. [hard]

**Success criteria:**

1. **[b96b17cd]** (weight=1) The SIRD task is available such that synthetic data can be sampled
2. **[6c80714a]** (weight=1) In the SIRD task, a uniform prior is imposed on the global variables $\gamma, \delta$ denoted as $\gamma, \delta \sim \text{Unif}(0, 0.5)$
3. **[22bc638a]** (weight=1) In the SIRD task, for the time-dependent contact rate, $\hat{\beta} \sim \mathcal{G}(0, k)$ is first sampled from a gaussian prior with $k$ representing an RBF kernel defined as $k(t_1, t_2) = 2.5^2 \exp\left(-\frac{1}{2} \frac{\|t_1 - t_2\|^2}{7^2}\right)$, then is transformed via a sigmoid function
4. **[4332dc3c]** (weight=1) In the SIRD task, the contact rate is implemented to vary over time, whereas the recovery and death rate are constant in time.
5. **[19f4319f]** (weight=1) In the SIRD task, observational data is modeled with log-normal noise with a mean of $S(t)$ and a standard deviation of $\sigma=0.05$
6. **[a0b66551]** (weight=1) The Simformer used for all experiments in Section 4.3 has 8 layers
7. **[e0c85d33]** (weight=1) The Simformer used in Section 4.3 uses the dense attention mask
8. **[a0864d9d]** (weight=1) Five synthetic observations are generated from infected, recovered, and deceased individuals at random times
9. **[78909e7b]** (weight=1) Given the five synthetic observations, the Simformer is applied to obtain samples from the posterior distribution of parameters as well as posterior predictive samples for unobserved  infected, recovered, and deceased values on a regular time grid from 0 to 40
10. **[81423255]** (weight=2) The mean of the death, recovery and contact rate parameters is somewhat close to the true parameter that generated the observations, using the Simformer given the five synthetic observations
11. **[eeb98ce1]** (weight=2) The mean of the infected, recovered and death population densities accurately model the sampled observations, using the Simformer given the five synthetic observations
12. **[a4c1f3af]** (weight=1) Synthetic observations consisting of four measurements of the time-dependent contact rate parameter is generated and a single synthetic observation of death population is generated
13. **[aa314a14]** (weight=2) The Simformer estimated realistic death and recovery rates, using the Simformer given the five synthetic observations
14. **[6e727597]** (weight=2) The predicted mean intercepts all four measurements of the time-dependent contact rate parameter, using the Simformer given the five synthetic observations
15. **[296dadfa]** (weight=2) The predicted mean of the death population intercepts the synthetic observation, using the Simformer given the five synthetic observations

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/all-in-one_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: all-in-one

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
