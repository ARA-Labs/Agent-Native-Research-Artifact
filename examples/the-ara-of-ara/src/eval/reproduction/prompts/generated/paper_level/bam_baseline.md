# Full Paper Reproduction: bam

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bam_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bam_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/bam.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/bam` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bam_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the Batch and Match (BaM) algorithm for variational inference with full-covariance Gaussian families, following Algorithm 1. Implement the batch step (sampling from the current Gaussian, computing target scores, accumulating score statistics per equations 6-7) and the match step (constructing U and V matrices per equations 10-11, solving the quadratic matrix equation for the covariance update, and updating the mean per equations 12-13). Include the optional low-rank solver for B < D (Lemma B.3). The implementation should accept batch size, inverse regularization (learning rate), target score function, initial mean, and initial covariance as inputs. [easy]

**Success criteria:**

1. **[bam-inte]** (weight=1) BaM has been implemented such that, at minimum, it takes batch size, inverse regularization (learning rate), the target score function, the initial mean and the initial covariance as input and outputs the estimated variational parameters.
2. **[bam-batc]** (weight=1) The 'batch' step in BaM has been implemented such that at each iteration the current estimated mean and covariance matrix are used to sample $z_b$ from a Gaussian for $b = 1, \dots, B$, where B is the batch size.
3. **[bam-batc]** (weight=1) The 'batch' step in BaM has been implemented such that at each iteration the "score" ($\nabla \log (p)$, where $p$ is the density of the target distribution)) can be and is computed for each sampled $z_b$.
4. **[bam-batc]** (weight=1) The 'batch' step in BaM has been implemented such that the sample statistics are accumulated following equations (6) and (7), as shown in step 5 of Algorithm 1.
5. **[bam-qm-e]** (weight=2) The 'match' step in BaM has been implemented such that at each iteration, the U and V matrices have been implemented using the accumulated statistics from the 'batch' step, as outlined in equations (10) and (11) and in step 6 of Algorithm 1.
6. **[bam-upda]** (weight=2) The 'match' step in BaM has been implemented such that at each iteration, the U and V matrices are used along with the accumulated statistics and the inverse regularization (learning rate) to update the estimated mean and covariance using equations (12) and (13) as shown in step 7 of algorithm 1.
7. **[bam-low-]** (weight=1) The BaM 'match' step has been implemented such that it optionally supports updating covariance using the update in Lemma B.3, asserting that B<D
8. **[6320b786]** (weight=1) BaM has been implemented such that it generally follows the steps in Algorithm 1.

### Subtask 2 of 10: Implement the three baseline variational inference algorithms: (1) ADVI with ELBO estimation via the reparameterization trick and ADAM-based gradient updates (Algorithm 2); (2) ADVI Score variant using score-based divergence loss instead of ELBO; (3) ADVI Fisher variant using Fisher divergence loss instead of ELBO; and (4) Gaussian Score Matching (GSM) with per-sample rank-1 covariance updates and partial-update averaging (Algorithm 3). All algorithms should operate on full-covariance Gaussian variational families. [easy]

**Success criteria:**

1. **[advi-set]** (weight=1) ADVI is implemented such that, at minimum, it takes batch size, a learning rate or learning rate schedule, the unnormalized target log density, the initial mean and the initial covariance as input and outputs the estimated variational parameters.
2. **[advi-sam]** (weight=1) ADVI has been implemented such that at each iteration, a mini-batch of samples is drawn from the current approximate distribution $q_{t}$, a Gaussian with some mean $\mu_{t}$ and covariance $\Sigma_{t}$.
3. **[advi-elb]** (weight=1) ADVI has been implemented such that at each iteration, a stochastic estimate of the (negative) Evidence Lower Bound (ELBO) is computed using the reparameterization trick or an equivalent approach for samples \(z_b\sim q_{t}\). Specifically, the code forms \(-\sum_b [\log p(z_b) - \log q_t(z_b)]\).
4. **[advi-upd]** (weight=1) ADVI has been implemented such that the gradient of the negative ELBO (with respect to the variational parameters) is used to update the variational parameters (e.g. via the Adam optimizer) as shown in step 5 of Algorithm 2
5. **[advi-has]** (weight=1) Overall, the implemented ADVI procedure follows the logic of Algorithm 2
6. **[28288cd0]** (weight=2) Automatic Differentiation Variational Inference (ADVI) "Score" variant has been implemented, such that it is identical to the ADVI implementation but rather than using ELBO loss, it uses score-based divergence.
7. **[2b23a5ca]** (weight=2) Automatic Differentiation Variational Inference (ADVI) "Fisher" variant has been implemented, such that it is identical to the ADVI implementation but rather than using ELBO loss, it uses Fisher divergence
8. **[gsm-inte]** (weight=1) GSM has been implemented such that it takes, at minimum, a batch size, the unnormalized target density, the initial mean and the initial covariance as input and outputs the estimated variational parameters.
9. **[gsm-iter]** (weight=1) GSM has been implemented such that at each iteration, a mini-batch of samples is drawn from the current approximate distribution $q_{t}$, a Gaussian with some mean $\mu_{t}$ and covariance $\Sigma_{t}$.
10. **[gsm-scor]** (weight=1) GSM has been implemented such that at each iteration, for each sampled $z_b$ the target distribution's score \$s_b = \nabla \log \tilde{p}(z_b)$ is computed
11. **[c8d8bf97]** (weight=1) GSM has been implemented such that at each iteration, for each sampled $z_b$, the updated for mean and covariance are estimated following steps 6 and 7 of Algorithm 3.
12. **[gsm-part]** (weight=1) GSM has been implemented such that each iteration, the variational mean and covariance are updated following step 9 of Algorithm 3.
13. **[gsm-has-]** (weight=1) Overall, the GSM procedure has been implemented so that it follows the main steps of Algorithm 3.

### Subtask 3 of 10: Implement the Gaussian target experiment infrastructure for Figure 5.1. Create Gaussian target distributions at D=4 and D=16, compute their score functions (analytically or via autodiff), implement forward and reverse KL divergence measurement between estimated and target Gaussians, and set up the experimental harness for BaM with learning rate lambda=BD, 10 seeded runs, and at least 10,000 iterations per run. [easy]

**Success criteria:**

1. **[50edd5b6]** (weight=1) Code has been implemented such that 4-dimensional Gaussian distributions can be used as target distributions
2. **[92c9368d]** (weight=1) Code has been implemented such that 16-dimensional Gaussian distributions can be used as target distributions
3. **[d6b2f005]** (weight=1) Code has been implemented such that the score function for a 4-dimensional Gaussian distribution can be computed (either analytically or with an autodiff solution)
4. **[c7b901f3]** (weight=1) Code has been implemented such that the score function for a 16-dimensional Gaussian distribution can be computed (either analytically or with an autodiff solution)
5. **[337c5085]** (weight=1) Code has been implemented for measuring the forward and reverse empirical KL divergences between two distributions
6. **[62a0b2d7]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a D-dimensional Gaussian distribution, the learning rate can be set to DB, where B is the batch size
7. **[39daebb5]** (weight=1) Code has been implemented such that the forward empirical KL divergences between the estimated and target posterior can be measured at each iteration when using BaM to estimate the posterior of a D-dimensional Gaussian distribution
8. **[71097d28]** (weight=1) Code has been implemented such that the reverse empirical KL divergences between the estimated and target posterior can be measured at each iteration when using BaM to estimate the posterior of a D-dimensional Gaussian distribution
9. **[3e177584]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a D-dimensional Gaussian distribution, BaM VI can be run for at least 10E4 iterations
10. **[40da5875]** (weight=1) Code has been implemented such that 10 separate seeded runs of BaM VI for estimating the posterior of a D-dimensional Gaussian distribution over some number of iterations can be run.

### Subtask 4 of 10: Run BaM at batch size B=300 with grid-searched learning rate on the pre-trained CIFAR-10 VAE posterior (D=256) for 1000 iterations. Measure reconstruction MSE versus iterations. Also run amortized VI (trained encoder) as a baseline. Verify that BaM with B=300 converges to lower MSE than amortized VI, demonstrating full-covariance VI advantage over factorized Gaussian on deep generative models. [medium]

**Success criteria:**

1. **[4b88bdfd]** (weight=1) Code has been implemented such that the estimated mean from BaM can be input into the decoder at each iteration so to obtain the reconstructed image at that iteration
2. **[c447e67b]** (weight=1) Code has been implemented such that the MSE between reconstructed image obtained from BaM and the sampled test image can be computed at each iteration
3. **[9136b526]** (weight=1) Code has been implemented such that when using BaM to reconstruct the sampled test image, BaM can be run for at least 1000 iterations
4. **[65d88f8d]** (weight=1) Code has been implemented such that BaM can be run at batch size 300 to estimate the posterior mean needed for reconstructing the sampled test image
5. **[50ae9c10]** (weight=1) Code has been implemented such that a preliminary grid search on 100 iterations can be run for determining the optimal learning rate for using BaM at batch size 300 to estimate the posterior mean needed for reconstructing the sampled test image
6. **[f3ebd402]** (weight=1) The optimal learning rate for using BaM to estimate the posterior mean needed for reconstructing the sampled test image with batch size 300 has been determined using a grid search
7. **[0bd5bc5f]** (weight=1) BaM has been run at batch size 300 to estimate the posterior mean needed for reconstructing the sampled test image
8. **[143b6d2d]** (weight=1) When using BaM to estimate the posterior mean needed for reconstructing the sampled test image with a batch size of 300, at least at least 1000 iterations of BaM have been run.
9. **[ad5934b0]** (weight=1) When using BaM to estimate the posterior mean needed for reconstructing the sampled test image with a batch size of 300, the MSE between the reconstructed image and the sampled test image has been measured at each iteration
10. **[97ed714b]** (weight=1) Code has been implemented such that the estimated mean from AVI (the trained encoder network) can be input into the decoder so to obtain the reconstructed image
11. **[1a663a4f]** (weight=1) AVI (the trained encoder network) has been run to estimate the posterior mean needed for reconstructing the sampled test image
12. **[9d3ca042]** (weight=1) When using AVI (the trained encoder network) to estimate the posterior mean needed for reconstructing the sampled test image, the MSE between the reconstructed image and the sampled test image has been measured
13. **[949cbdd8]** (weight=1) The MSE between the reconstructed image and the sampled test image measured over the VI iterations for BaM at batch size 10 shows that BaM performs poorly (MSE greater than 0.2) at smaller batch sizes, i.e. at a batch size of 10.
14. **[d520be6a]** (weight=1) The MSE between the reconstructed image and the sampled test image measured over the VI iterations for BaM, ADVI and AVI at batch sizes 10, 100 and 300 show that in general either BaM or ADVI or both achieve a MSE than AVI.

### Subtask 5 of 10: Run BaM on 4-dimensional Gaussian targets at batch sizes B=2 and B=5 with constant learning rate lambda=BD for at least 10,000 iterations over 10 seeded runs. Measure forward and reverse KL divergence at each iteration. Verify that BaM converges to near-zero KL, and that larger batch size (B=5) converges faster than smaller batch size (B=2), consistent with the paper's exponential convergence theory (Theorem 4.1). [medium]

**Success criteria:**

1. **[c5574df9]** (weight=1) Code has been implemented for using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2
2. **[1876119e]** (weight=1) BaM has been run to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2
3. **[116b2cae]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2, the learning rate was set to BD
4. **[4c09eede]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2, the forward empirical KL divergence has been measured at each iteration.
5. **[8f83d494]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2, the reverse empirical KL divergence has been measured at each iteration.
6. **[db63a034]** (weight=1) 10 seeded runs using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2 have been run.
7. **[fbdb544e]** (weight=1) Code has been implemented for using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5
8. **[09e0158e]** (weight=1) BaM has been run to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5
9. **[7e41d3f2]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5, the learning rate was set to BD
10. **[723c33ff]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5, the forward empirical KL divergence has been measured at each iteration.
11. **[927f15c3]** (weight=1) When using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5, the reverse empirical KL divergence has been measured at each iteration.
12. **[c9e6dd41]** (weight=1) 10 seeded runs using BaM to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 5 have been run.
13. **[afaa90e8]** (weight=1) The forward and reverse KL divergence between target and estimated Gaussian distributions measured over VI iterations for BaM and ADVI show that BaM converges orders of magnitude earlier (in terms of number of iterations) than ADVI.

### Subtask 6 of 10: Run ADVI (ELBO) with ADAM at grid-searched optimal learning rate on 4-dimensional Gaussian targets at batch size B=2 for at least 10,000 iterations over 10 seeded runs. Measure forward and reverse KL divergence at each iteration. Compare against BaM results from T4 to verify that BaM converges to near-zero KL in significantly fewer gradient evaluations than ADVI, often by orders of magnitude. [medium]

**Success criteria:**

1. **[e7325915]** (weight=1) Code has been implemented such that when using ADVI to estimate the posterior of a D-dimensional Gaussian distribution, ADVI can be run for at least 10E4 iterations
2. **[a6f9be76]** (weight=1) Code has been implemented such that the forward and reverse empirical KL divergences between the estimated and target posterior can be measured at each iteration when using ADVI to estimate the posterior of a D-dimensional Gaussian distribution
3. **[f032d17c]** (weight=1) Code has been implemented such that 10 separate seeded runs of ADVI for estimating the posterior of a D-dimensional Gaussian distribution over some number of iterations can be run.
4. **[e7397fe9]** (weight=1) Code has been implemented for using ADVI to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2
5. **[61156dc6]** (weight=1) Code has been implemented such that a grid search can be run for determining the optimal learning rate for using ADVI to estimate the posterior of a 4-dimensional Gaussian distributionwith batch size 2.
6. **[a315b608]** (weight=1) The optimal learning rate for using ADVI to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2 has been determined using a grid search
7. **[379a38a5]** (weight=1) ADVI has been run to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2
8. **[24ec6ae5]** (weight=1) When using ADVI to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2, the learning rate was set to the learning rate determined by the grid search.
9. **[ef371648]** (weight=1) When using ADVI to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2, the forward and reverse empirical KL divergence between the estimated posterior and the target posterior has been measured at each iteration
10. **[b1ce0df4]** (weight=1) 10 seeded runs using ADVI to estimate the posterior of a 4-dimensional Gaussian distribution with batch size 2 have been run.

### Subtask 7 of 10: Run BaM on 10-dimensional sinh-arcsinh non-Gaussian targets with skew s=0.2 (easy) and s=1.8 (hard) at batch sizes B=5 and B=10 with decaying learning rate lambda_t=BD/(t+1). Measure forward and reverse KL divergence over 10 seeded runs of at least 10,000 iterations each. Verify that (a) BaM converges on both easy and hard non-Gaussian targets, and (b) larger batch size B=10 provides more stable convergence than B=5, especially for high skew s=1.8. [medium]

**Success criteria:**

1. **[ff269cb7]** (weight=1) Code has been implemented such that 10-dimensional sinh-arcsinh normal distributions with a normal tail ($t=1$) and skew $s=0.2$ can be used as target distributions
2. **[82a1992c]** (weight=1) Code has been implemented such that 10-dimensional sinh-arcsinh normal distributions with a normal tail ($t=1$) and skew $s=1.8$ can be used as target distributions
3. **[5b909bab]** (weight=1) Code has been implemented such that the score function for a 10-dimensional sinh-arcsinh normal distribution can be computed (either analytically or with an autodiff solution) with a normal tail ($t=1$) and skew $s=0.2$
4. **[a1e6e69f]** (weight=1) Code has been implemented such that the score function for a 10-dimensional sinh-arcsinh normal distribution can be computed (either analytically or with an autodiff solution) with a normal tail ($t=1$) and skew $s=1.8$
5. **[9dad0b0e]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a given 10-dimensional sinh-arcsinh normal distribution, the learning rate can be set to $10B/(t+1)$, where B is the batch size and t is the iteration
6. **[18ac0834]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a given 10-dimensional sinh-arcsinh normal distribution, BaM VI can be run for at least 10E4 iterations
7. **[6c1197c7]** (weight=1) Code has been implemented such that 10 separate seeded runs of BaM VI for estimating the posterior of a given 10-dimensional sinh-arcsinh normal distribution over some number of iterations can be run.
8. **[28d977ff]** (weight=1) Code has been implemented for using BaM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=0.2$ with batch size 5
9. **[f4f43f48]** (weight=1) BaM has been run to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=0.2$ with batch size 5
10. **[47bfc7bf]** (weight=1) 10 seeded runs using BaM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=0.2$ with batch size 5 have been run.
11. **[d8e5e825]** (weight=1) Code has been implemented for using BaM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5
12. **[99eb13b1]** (weight=1) BaM has been run to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5
13. **[c4c35868]** (weight=1) 10 seeded runs using BaM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5 have been run.
14. **[9f8f0bec]** (weight=1) The forward and reverse KL divergence between target and estimated sinh-arcsinh normal distributions with normal tails ($t=1$) and varying skews measured over VI iterations for BaM and ADVI show that, compared to ADVI, BaM converges to a higher value in terms of forward KL divergence and to a similar value in terms of reverse KL divergence

### Subtask 8 of 10: Run GSM on 10-dimensional sinh-arcsinh non-Gaussian targets with skew s=1.8 at batch size B=5 for at least 10,000 iterations over 10 seeded runs. Measure forward and reverse KL divergence. Compare against BaM results from T6 to verify that GSM's reverse KL diverges for high skew s=1.8 while BaM remains stable, demonstrating BaM's superior robustness on difficult non-Gaussian targets. [hard]

**Success criteria:**

1. **[d712e1e2]** (weight=1) Code has been implemented such that when using GSM to estimate the posterior of a given 10-dimensional sinh-arcsinh normal distribution, GSM VI can be run for at least 10E4 iterations
2. **[744581d5]** (weight=1) Code has been implemented such that 10 separate seeded runs of GSM VI for estimating the posterior of a given 10-dimensional sinh-arcsinh normal distribution over some number of iterations can be run.
3. **[12437269]** (weight=1) Code has been implemented for using GSM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5
4. **[a98484f2]** (weight=1) GSM has been run to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5
5. **[0f5315a6]** (weight=1) When using GSM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5, at least at least 10E4 iterations of GSM VI have been run.
6. **[fa911b45]** (weight=1) When using GSM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5, the forward empirical KL divergence has been measured at each iteration.
7. **[4299c0e1]** (weight=1) When using GSM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5, the reverse empirical KL divergence has been measured at each iteration.
8. **[773b436c]** (weight=1) 10 seeded runs using GSM to estimate the posterior of a 10-dimensional sinh-arcsinh normal distribution with tail $t=1$ and skew $s=1.8$ with batch size 5 have been run.
9. **[71fd6df1]** (weight=1) The forward and reverse KL divergence between target and estimated sinh-arcsinh normal distributions with normal tails ($t=1$) and varying skews measured over VI iterations for BaM and ADVI show that BaM converges faster (in terms of number of iterations) than ADVI.
10. **[bec65857]** (weight=1) The reverse KL divergence between target and estimated sinh-arcsinh normal distributions with no skew ($s=0$) and varying tails measured over VI iterations for BaM, GSM, ADVI, Score and Fisher show that all methods converge to similar values

### Subtask 9 of 10: Reproduce the posteriorDB posterior inference experiment (Figure 5.3). Load the arK (D=7) and eight-schools-centered (D=10) Stan models, obtain HMC reference posteriors, then run BaM at batch sizes B=8 and B=32 with decaying learning rate lambda_t=BD/(t+1). Compute relative mean error and relative SD error versus gradient evaluations over 5 seeded runs. Verify that BaM with B=32 converges faster and more stably than BaM with B=8. [hard]

**Success criteria:**

1. **[f9f9945c]** (weight=1) Code has been implemented such reference samples generated with Hamiltonian Monte Carlo (HMC) can be sampled for the PosteriorDB `ark` problem, at dimension D=7
2. **[6ffc9f02]** (weight=1) Code has been implemented such reference samples generated with Hamiltonian Monte Carlo (HMC) can be sampled for the PosteriorDB `eight-schools-centered` problem, at dimension D=10
3. **[7239250f]** (weight=1) Code has been implemented such that the score function for the PosteriorDB `ark` problem, at dimension D=7, can be computed (likely via bridgestan)
4. **[c840a1e2]** (weight=1) Code has been implemented such that the score function for the PosteriorDB `eight-schools-centered` problem, at dimension D=10, can be computed (likely via bridgestan)
5. **[5afd823b]** (weight=1) Code has been implemented such that the relative mean error between a given pair of estimated and HMC posterior parameters can be computed, as outlined in equation (242) in Appendix E.5
6. **[8cb1d179]** (weight=1) Code has been implemented such that the relative standard error between a given pair of estimated and HMC posterior parameters can be computed, as outlined in equation (242) in Appendix E.5
7. **[709db886]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a given PosteriorDB problem, the learning rate can be set to $DB/(t+1)$, where B is the batch size and t is the iteration
8. **[497dfe00]** (weight=1) Code has been implemented such that when using BaM to estimate the posterior of a given PosteriorDB problem, BaM can be run for at least 10E4 iterations
9. **[f7954dbd]** (weight=1) Code has been implemented such that 5 separate seeded runs of BaM for estimating the posterior of a given of a given PosteriorDB problem over some number of iterations can be run.
10. **[ed644299]** (weight=1) Code has been implemented for using BaM to estimate the posterior of the PosteriorDB `ark` problem, at dimension D=7, with a batch size of 8
11. **[5c51279d]** (weight=1) When using BaM to estimate the posterior of the PosteriorDB `ark` problem, at dimension D=7, with a batch size of 8, the learning rate was set to $BD/(t+1)$
12. **[42b6b19f]** (weight=1) When using BaM to estimate the posterior of the PosteriorDB `ark` problem, at dimension D=7, with a batch size of 8, the relative mean error between the estimated posterior and the HMC posterior has been measured at each iteration
13. **[24d3f024]** (weight=1) 10 seeded runs using BaM to estimate the posterior of the PosteriorDB `ark` problem, at dimension D=7, with a batch size of 8 have been run.
14. **[b686ecb8]** (weight=1) The relative mean error between HMC and estimated PosteriorDB problem posteriors measured over VI iterations for BaM and ADVI show BaM outperforms ADVI, converging earlier (in terms of number of iterations) to lower relative mean errors.
15. **[5822d5a9]** (weight=1) The relative mean error and relative standard error between HMC and estimated PosteriorDB problem posteriors measured over VI iterations for BaM, ADVI and GSM show that in general the same trends can be observed for relative mean error and relative standard error, with the exception of the "hierarchical" `eight-schools-centered` problem where BaM converges to a higher relative standard error than GSM or ADVI.

### Subtask 10 of 10: Implement and pre-train a 5-layer convolutional VAE on CIFAR-10 with Gaussian likelihood (sigma^2=0.1, latent D=256) for 100 epochs following the architecture described in the addendum. Sample a test image and implement the posterior score function s(z)=nabla_z log p(z|x), the MSE metric for image reconstruction, and the decoder pipeline to convert variational mean estimates into reconstructed images. [hard]

**Success criteria:**

1. **[6679061e]** (weight=1) Code has been implemented such that the CIFAR 10 dataset can be used
2. **[8789e782]** (weight=1) Code has been executed such that the CIFAR 10 dataset can be used (e.g. the dataset has been downloaded and other experiments in the reproduction can use it)
3. **[b8517162]** (weight=1) A variational autoencoder architecture has been implemented such that the encoder and decoder each consist of 5 convolutional layers.
4. **[fd19a4f4]** (weight=1) The generative model has been implemented such that it models the images using a Gaussian Likelihood over the distribution of images
5. **[c8f3e04d]** (weight=1) The generative model's gaussian likelihood has been implemented such that the covariance is fixed to $\sigma^2 I$, where $I$ is the identity matrix and $\sigma^2$ is fixed to 0.1
6. **[a8db3546]** (weight=1) The variational autoencoder hyperparameters and architecture generally align with what is outlined in the addendum
7. **[5bcc62df]** (weight=1) Code has been implemented such that a VAE can be trained on the CIFAR 10 image dataset training split following the standard VAE training procedure from Kingma & Welling, 2014 described in Appendix E.6
8. **[479536e1]** (weight=1) Code has been executed such that a VAE has been trained on the CIFAR 10 image dataset training split following the standard VAE training procedure from Kingma & Welling, 2014 described in Appendix E.6
9. **[81ac357b]** (weight=1) Code has been implemented such that the score function for the posterior ($s(z) = \nabla_z \log p(z \mid x) = \nabla_z \log p(z) + \nabla_z \log p(x \mid z), $ where $p(x \mid z)$ is the decoder network) can be computed (likely via an autodiff solution)
10. **[1d9d9df5]** (weight=1) Code has been implemented such that the Mean Squared Error (MSE) between two images can be computed
11. **[7beb3412]** (weight=1) Code has been implemented such that an image x' can be sampled from the CIFAR 10 image dataset test split
12. **[fb40e7cd]** (weight=1) An image x' has been sampled from the CIFAR 10 image dataset test split
13. **[30cfc3c2]** (weight=1) Code has been implemented such that the estimated mean from a given VI method can be input into the decoder so to obtain the reconstructed image

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bam_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: bam

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
