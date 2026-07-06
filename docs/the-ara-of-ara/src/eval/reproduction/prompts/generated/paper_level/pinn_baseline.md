# Full Paper Reproduction: pinn

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/pinn_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/pinn_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/pinn.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/pinn` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/pinn_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement a PINN for the convection equation (beta=40). Build a 3-hidden-layer MLP with tanh activations and Xavier normal initialization, supporting widths in {50, 100, 200, 400}. Implement the PINN loss function as the non-linear least squares objective from section 2.1, with the relevant differential operator and boundary/initial condition operators from Appendix A.1. Implement the data sampling scheme: 10000 residual points randomly sampled from a 255x100 grid, 257 initial condition points, and 101 boundary condition points (sampled once before training). Implement support for training with the Adam optimizer for 41000 iterations across 5 random seeds, with learning rate grid-searchable over {1e-5, 1e-4, 1e-3, 1e-2, 1e-1}. Implement final loss and L2RE measurement. [easy]

**Success criteria:**

1. **[a6ce62f7]** (weight=1) The MLP for solving the Convection problem has been implemented such that it can have 3 hidden layers, each of equal width
2. **[f4b24398]** (weight=1) The MLP for solving the Convection problem has been implemented such that the width of its hidden layers can be set to 50, 100, 200 or 400. All hidden layers have the same width.
3. **[5c307e8d]** (weight=1) The MLP for solving the Convection problem has been implemented such that there can be a tanh activation function between each hidden layer
4. **[60faf3ea]** (weight=1) The MLP for solving the Convection problem has been implemented such that the MLP's weights can be initialized using Xavier normal initialization, i.e. $W \sim \mathcal{N}(0, \frac{2}{\text{fan\_in} + \text{fan\_out}}) $ where $fan\_in$ = number of input units for the layer and $fan\_out$ = number of output units for the layer. The biases are initialized as 0.
5. **[342b68e9]** (weight=1) The loss function used for training the MLP for solving the Convection problem has been implemented such that it corresponds to the "non-linear least squares problem" described in section 2.1, with the relevant differential operator and boundary/initial condition operators outlined in Appendix A.1
6. **[a3c75cd0]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem, training can be run for 41000 training iterations per seed.
7. **[f479ecec]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem, the final L2RE can be measured and is properly implemented as outlined in section 2.2 with the relevant ground truth analytical solution outlined in Appendix A.1
8. **[0447a800]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem, 5 random seeds of training can be run
9. **[7936a6fe]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem, the final loss can be measured
10. **[09f36ab9]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem, at each iteration the MLP can be trained on a fixed set of 10000 residual points randomly sampled from a 255 x100 grid on the interior of the problem domain, 257 equally spaced points for each initial condition and 101 equally spaced points for each boundary condition. The sampling is done once, before training begins, and the sampled points are kept fixed throughout training. Domain, boundaries and initial conditions should match Appendix A.1
11. **[d93ee7b8]** (weight=1) Code has been implemented such that to train an MLP to solve the Convection problem, Adam can be used as the optimizer
12. **[657521ec]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the Adam optimizer, the learning rate of the Adam optimizer can be set to 1E-5, 1E-4, 1E-3, 1E-2, or 1E-1

### Subtask 2 of 10: Implement PINNs for the reaction and wave equations. For each PDE, build a 3-hidden-layer MLP with tanh activations and Xavier normal initialization, supporting widths in {50, 100, 200, 400}. Implement the PINN loss function as the non-linear least squares objective from section 2.1, with the relevant differential operators from Appendix A.2 (reaction) and A.3 (wave). Implement data sampling, 41000-iteration training support, 5-seed repetition, and final loss plus L2RE measurement for each PDE domain. [easy]

**Success criteria:**

1. **[510d01fa]** (weight=1) The MLP for solving the reaction problem has been implemented such that it has exactly 3 hidden layers, each of equal width
2. **[11811fd7]** (weight=1) The MLP for solving the reaction problem has been implemented such that the width of its hidden layers can be set to 50, 100, 200 or 400. All hidden layers have the same width.
3. **[5c307e8d]** (weight=1) The MLP for solving the reaction problem has been implemented such that there is a tanh activation function between each hidden layer
4. **[60faf3ea]** (weight=1) The MLP for solving the reaction problem has been implemented such that the MLP's weights are initialized using Xavier normal initialization, i.e. $W \sim \mathcal{N}(0, \frac{2}{\text{fan\_in} + \text{fan\_out}}) $ where $fan\_in$ = number of input units for the layer and $fan\_out$ = number of output units for the layer. The biases are initialized as 0.
5. **[7f76f889]** (weight=1) The loss function used for training the MLP for solving the reaction problem has been implemented such that it corresponds to the "non-linear least squares problem" described in section 2.1, with the relevant differential operator and boundary/initial condition operators outlined in Appendix A.2
6. **[f09e6209]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem, training can be run for 41000 training iterations per seed.
7. **[20e48ec9]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem, the final L2RE can be measured and is properly implemented as outlined in section 2.2 with the relevant ground truth analytical solution outlined in Appendix A.2
8. **[b1adc8d3]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem, 5 random seeds of training can be run
9. **[37f3734c]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem, the final loss can be measured
10. **[ba0d26b5]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem, at each iteration the MLP can be trained on a fixed set of 10000 residual points randomly sampled from a 255 x100 grid on the interior of the problem domain, 257 equally spaced points for each initial condition and 101 equally spaced points for each boundary condition. The sampling is done once, before training begins, and the sampled points are kept fixed throughout training. Domain, boundaries and initial conditions should match Appendix A.2

### Subtask 3 of 10: Implement stochastic Lanczos quadrature (SLQ) for Hessian spectral density estimation and run the total-loss Hessian analysis (Section 5.1). For the best trained model on each PDE (convection, reaction, wave), estimate the spectral density of the total PINN loss Hessian. Confirm that all three PDEs show (1) significant spectral density near eigenvalue zero and (2) large outlier eigenvalues (>1e3), indicating severe ill-conditioning of the PINN loss landscape. [easy]

**Success criteria:**

1. **[87fa24bb]** (weight=2) Code has been implemented such that the spectral density of the hessian of a loss function w.r.t. model parameters can be estimated. (Off-the-shelf libraries like PyHessian are allowed).
2. **[b2308687]** (weight=1) The spectral density of the hessian of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Convection problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.1
3. **[39e34f7c]** (weight=1) The spectral density of the hessian of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Reaction problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.2
4. **[9e32ac3c]** (weight=1) The spectral density of the hessian of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Wave problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.3
5. **[6c752611]** (weight=2) The spectral density measured for each of the successfully studied problem domains shows significant spectral density near eigenvalues of 0
6. **[c73838b8]** (weight=2) The spectral density measured for each of the successfully studied problem domains shows large outlier eigenvalues (e.g. with values > 1e3)

### Subtask 4 of 10: Reproduce the per-iteration wall-clock timing comparison between L-BFGS and NNCG (Table 3). Implement per-iteration timing measurement. Measure and report per-iteration wall-clock times for L-BFGS and NNCG training on each of the three PDE domains (convection, reaction, wave). Confirm that NNCG is at least 5x slower per iteration than L-BFGS across all problem domains, establishing the computational cost tradeoff between NNCG's superior convergence and its higher per-step expense. [easy]

**Success criteria:**

1. **[81d1f400]** (weight=1) Code has been implemented for measuring the per-iteration wall-clock time during training
2. **[2192ccec]** (weight=1) Per-iteration wall-clock time has been measured when training using the L-BFGS optimizer on the convection problem domain
3. **[33402091]** (weight=1) Per-iteration wall-clock time has been measured when training using the L-BFGS optimizer on the reaction problem domain
4. **[8b03d367]** (weight=1) Per-iteration wall-clock time has been measured when training using the L-BFGS optimizer on the wave problem domain
5. **[942ace27]** (weight=1) Per-iteration wall-clock time has been measured when training using the NNCG optimizer on the convection problem domain
6. **[27024621]** (weight=1) Per-iteration wall-clock time has been measured when training using the NNCG optimizer on the reaction problem domain
7. **[2b311ead]** (weight=1) Per-iteration wall-clock time has been measured when training using the NNCG optimizer on the wave problem domain
8. **[e7d45c85]** (weight=2) The measured per-iteration wall-clock times show that NNCG is slower than L-BFGS across all problem domains by at least 5x

### Subtask 5 of 10: Train and evaluate PINNs with the Adam optimizer on the convection equation. Run a scoped sweep with network width 100 across 3 learning rates {1e-4, 1e-3, 1e-2}, training for 41000 iterations with 5 random seeds each. For each (lr, seed) configuration, measure final training loss and L2 relative error (L2RE) against the analytical solution. Record all results to verify the loss-L2RE relationship across the learning rate sweep. [medium]

**Success criteria:**

1. **[e26aa4a5]** (weight=3) Code has been executed such that a three-hidden-layer MLP with a layer width of 100 has been trained to solve the Convection problem using the Adam optimizer with a learning rate of 1E-4, and the final loss and L2RE have been measured
2. **[089dfd68]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-4, 5 random seeds were trained
3. **[7b8cbc27]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-4, it was trained for 41000 training iterations per random seed.
4. **[8de8647a]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-4, at each iteration the MLP is trained on a fixed set of 10000 residual points randomly sampled from a 255x100 grid on the interior of the problem domain, 257 equally spaced points for each initial condition and 101 equally spaced points for each boundary condition. The sampling is done once, before training begins, and the sampled points are kept fixed throughout training. Domain, boundaries and initial conditions should match Appendix A.1
5. **[080093e3]** (weight=3) Code has been executed such that a three-hidden-layer MLP with a layer width of 100 has been trained to solve the Convection problem using the Adam optimizer with a learning rate of 1E-3, and the final loss and L2RE have been measured
6. **[6529bc3a]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-3, 5 random seeds were trained
7. **[23fce3c7]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-3, it was trained for 41000 training iterations per random seed.
8. **[cb417ae1]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-3, at each iteration the MLP is trained on a fixed set of 10000 residual points randomly sampled from a 255x100 grid on the interior of the problem domain, 257 equally spaced points for each initial condition and 101 equally spaced points for each boundary condition. The sampling is done once, before training begins, and the sampled points are kept fixed throughout training. Domain, boundaries and initial conditions should match Appendix A.1
9. **[33629705]** (weight=3) Code has been executed such that a three-hidden-layer MLP with a layer width of 100 has been trained to solve the Convection problem using the Adam optimizer with a learning rate of 1E-2, and the final loss and L2RE have been measured
10. **[dacf0520]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-2, 5 random seeds were trained
11. **[1fbe9746]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-2, it was trained for 41000 training iterations per random seed.
12. **[814ef0de]** (weight=1) Code has been executed such that when training a three-hidden-layer MLP with a layer width of 100 to solve the Convection problem using the Adam optimizer with a learning rate of 1E-2, at each iteration the MLP is trained on a fixed set of 10000 residual points randomly sampled from a 255x100 grid on the interior of the problem domain, 257 equally spaced points for each initial condition and 101 equally spaced points for each boundary condition. The sampling is done once, before training begins, and the sampled points are kept fixed throughout training. Domain, boundaries and initial conditions should match Appendix A.1

### Subtask 6 of 10: Implement the L-BFGS optimizer and Adam+L-BFGS(1k) combined training strategy for the convection equation. For L-BFGS, implement training with lr=1.0, history size (memory)=100, and strong Wolfe line search. For Adam+L-BFGS(1k), implement the schedule that trains with Adam for the first 1000 iterations then switches to L-BFGS for the remaining 40000 iterations, with the same L-BFGS hyperparameters. Verify the implementation supports the full convection training pipeline. [medium]

**Success criteria:**

1. **[878b5031]** (weight=2) Code has been implemented such that to train an MLP to solve the Convection problem, L-BFGS can be used as the optimizer
2. **[cd0861d3]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, a learning rate of 1.0 can be set
3. **[5208b0d8]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, a memory size of 100 can be set
4. **[1ba289ae]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, strong Wolfe line search can be used
5. **[2170e804]** (weight=2) Code has been implemented such that to train an MLP to solve the Convection problem, the Adam+L-BFGS (1k) optimizer setup can be used
6. **[dbeb4056]** (weight=2) Code has been implemented such that when training an MLP to solve the Convection problem using the Adam+L-BFGS (1k) optimizer setup, the learning rate of the Adam optimizer can be set to 1E-5, 1E-4, 1E-3, 1E-2, or 1E-1
7. **[7055f1bb]** (weight=2) Code has been implemented such that when training an MLP to solve the Convection problem, the optimizer can be set to be Adam for the first 1k steps after which it can be switched to L-BFGS for the remainder of training.
8. **[a0a7f42f]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, a learning rate of 1.0 can be set
9. **[98934fc8]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, a memory size of 100 can be set
10. **[8650cd8f]** (weight=1) Code has been implemented such that when training an MLP to solve the Convection problem using the L-BFGS optimizer, strong Wolfe line search can be used

### Subtask 7 of 10: Run the per-component Hessian spectral density analysis (Section 5.2) on the convection and reaction PDEs. Decompose the PINN loss into residual, initial condition, and boundary condition components. For the best trained model on each PDE, estimate the Hessian spectral density of each component separately. Confirm that (1) the residual component is the most ill-conditioned (largest maximum eigenvalue) and (2) the residual differential operator is the dominant source of the overall ill-conditioning, for both convection and reaction problems. [medium]

**Success criteria:**

1. **[7807ef1d]** (weight=1) The spectral density of the hessian of the residual component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Convection problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.1
2. **[8350eee7]** (weight=1) The spectral density of the hessian of the initial conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Convection problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.1
3. **[777acb6b]** (weight=1) The spectral density of the hessian of the boundary conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Convection problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.1
4. **[562c8925]** (weight=2) The spectral density of the loss components measured for the best model trained (as determined following the systematic approach outlined in the addendum) with Adam+L-BFGS (11k) on the Convection problem show that each component is ill-conditioned
5. **[b099274f]** (weight=2) The spectral density of the loss components measured for the best model trained (as determined following the systematic approach outlined in the addendum) with Adam+L-BFGS (11k) on the Convection problem show the residual loss component is the most ill-conditioned component.
6. **[95f3f58c]** (weight=1) The spectral density of the hessian of the residual component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Reaction problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.2
7. **[3816a6ca]** (weight=1) The spectral density of the hessian of the initial conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Reaction problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.2
8. **[54bbcad9]** (weight=1) The spectral density of the hessian of the boundary conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Reaction problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.2
9. **[164ad07f]** (weight=2) The spectral density of the loss components measured for the best model trained (as determined following the systematic approach outlined in the addendum) with Adam+L-BFGS (11k) on the Reaction problem show that each component is ill-conditioned
10. **[ef770d5c]** (weight=2) The spectral density of the loss components measured for the best model trained (as determined following the systematic approach outlined in the addendum) with Adam+L-BFGS (11k) on the Reaction problem show the residual loss component is the most ill-conditioned component.

### Subtask 8 of 10: Train the full optimizer comparison sweep on the reaction equation and reproduce the aggregate optimizer ranking (Table 1 / Figure 8 / Figure 2). Implement Adam, L-BFGS, and Adam+L-BFGS(1k) for the reaction PDE. Run sweeps across widths and learning rates. Produce the scatter plot of final loss vs L2RE across all (optimizer, width, seed) combinations (Figure 2), confirming the monotone loss-L2RE relationship. Verify that when selecting the best learning rate per optimizer-width pair, Adam+L-BFGS achieves the lowest final loss and L2RE (Table 1 / Figure 8). [hard]

**Success criteria:**

1. **[c6a729a2]** (weight=1) Code has been implemented such that to train an MLP to solve the reaction problem, Adam can be used as the optimizer
2. **[369f1a10]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem using the Adam optimizer, the learning rate of the Adam optimizer can be set to 1E-5, 1E-4, 1E-3, 1E-2, or 1E-1
3. **[762501f9]** (weight=2) Code has been implemented such that to train an MLP to solve the reaction problem, L-BFGS can be used as the optimizer
4. **[b5124c53]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem using the L-BFGS optimizer, a learning rate of 1.0 can be set
5. **[d783df52]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem using the L-BFGS optimizer, a memory size of 100 can be set
6. **[17620733]** (weight=1) Code has been implemented such that when training an MLP to solve the reaction problem using the L-BFGS optimizer, strong Wolfe line search can be used
7. **[e8863305]** (weight=2) Code has been implemented such that to train an MLP to solve the reaction problem, the Adam+L-BFGS (1k) optimizer setup can be used
8. **[fe1c592c]** (weight=2) Code has been implemented such that when training an MLP to solve the reaction problem using the Adam+L-BFGS (1k) optimizer setup, the learning rate of the Adam optimizer can be set to 1E-5, 1E-4, 1E-3, 1E-2, or 1E-1
9. **[93c89866]** (weight=2) Code has been implemented such that when training an MLP to solve the reaction problem, the optimizer can be set to be Adam for the first 1k steps after which it can be switched to L-BFGS for the remainder of training.
10. **[835d353d]** (weight=1) The final loss metrics recorded at the end the executed training sweep described in section 2.2 show that, when selecting the learning-rate configurations with the lowest loss for a given optimizer-width combination, across most network widths and problem domains, Adam+L-BFGS always achieves the lowest minimum loss compared to just using Adam or L-BFGS as the optimizer. Minimum loss is defined as described in the caption of Figure 8.
11. **[f5c37a0a]** (weight=1) The final L2RE metrics recorded at the end the executed training sweep described in section 2.2 show that, when selecting the learning-rate configurations with the lowest minimum L2RE for a given optimizer-width-problem-domain combination, across most network widths and problem domains, Adam+L-BFGS always achieves the lowest minimum L2RE compared to just using Adam or L-BFGS as the optimizer. Minimum L2RE is defined as described in the caption of Figure 8.
12. **[327e7ab9]** (weight=1) The final loss and L2RE from measured at the end of the training of MLPs trained on each of the successfully studied problem domains with various optimizers, learning rates and widths show that in general a lower loss corresponds to a lower L2RE.
13. **[81e9e6a6]** (weight=1) The final loss and L2RE from measured at the end of the training of MLPs trained on each of the successfully studied problem domains with various optimizers, learning rates and widths show that there are instances where despite measuring a loss close to 0, L2RE is measured to be close to 1

### Subtask 9 of 10: Implement L-BFGS preconditioner unrolling (Algorithm 2 from Appendix C.2) and reproduce the preconditioned Hessian spectral density analysis (Section 5.3 / Figure 7). Save L-BFGS directions, steps, and inverse inner products at end of training. Estimate the preconditioned Hessian spectral density (H_k * H_L) for all three PDEs, confirming at least 1000x reduction in maximum eigenvalue magnitude compared to the unpreconditioned Hessian. Additionally, run the per-component preconditioned analysis on the wave PDE, verifying reduced ill-conditioning for each loss component after preconditioning. [hard]

**Success criteria:**

1. **[9bbde4e1]** (weight=1) Code has been implemented such that at the end of training, the L-BFGS directions, steps and inverse of inner products are saved, as described in Appendix C.2
2. **[8401ecfc]** (weight=1) Code has been implemented such that the L-BFGS update can be unrolled as outlined in Algorithm 2 in Appendix C.2
3. **[899a3913]** (weight=1) Code has been implemented such that the spectral density of the hessian of a loss function w.r.t. model parameters after L-BFGS preconditioning can be estimated as outlined in Algorithm 3 in Appendix C.2
4. **[726fac50]** (weight=1) The spectral density of the hessian after preconditioning with L-BFGS of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Convection problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.1
5. **[f715505f]** (weight=1) The spectral density of the hessian after preconditioning with L-BFGS of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Reaction problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.2
6. **[c4956a9e]** (weight=1) The spectral density of the hessian after preconditioning with L-BFGS of the total PINN loss function w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Wave problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.3
7. **[64500f58]** (weight=2) The spectral density after preconditioning measured for each of the successfully studied problem domains shows a decrease by at least 1E3 in the maximum eigenvalues compared to the spectral density measured without preconditioning, and a smaller range of eigenvalues in general.
8. **[d6b2f36e]** (weight=1) The spectral density of the hessian after preconditioning of the residual component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Wave problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.3
9. **[b3ae9334]** (weight=1) The spectral density of the hessian after preconditioning of the initial conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Wave problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.3
10. **[ca411097]** (weight=1) The spectral density of the hessian after preconditioning of the boundary conditions component loss w.r.t. final model parameters has been estimated for the best model trained (as determined following the systematic approach outlined in the addendum) on the Wave problem domain with Adam+L-BFGS (11k), with the coefficients outlined in Appendix A.3
11. **[270c3033]** (weight=2) The spectral density of the hessian after preconditioning of the loss components measured for the best model trained (as determined following the systematic approach outlined in the addendum) with Adam+L-BFGS (11k) on the Wave problem show that each preconditioning improves the conditioning of each individual loss component, with lower maximum eigenvalues and a smaller range of eigenvalues compared to the spectral density measured without preconditioning.

### Subtask 10 of 10: Implement the NysNewton-CG (NNCG) optimizer and run the fine-tuning experiment (Section 7.3 / Table 2 / Figure 5). Implement the four NNCG components: RandomizedNystromApproximation (Algorithm 5), NystromPCG (Algorithm 6), Armijo line search (Algorithm 7), and the full NNCG loop (Algorithm 4). Implement gradient descent (GD) fine-tuning as a baseline. Starting from the best Adam+L-BFGS checkpoint for each PDE (convection, reaction, wave), run 2000 additional steps with both NNCG and GD. Verify that NNCG reduces loss by >10x while GD produces no improvement, confirming the benefit of second-order optimization where first-order methods stall. [hard]

**Success criteria:**

1. **[64647c33]** (weight=1) The RandomizedNystromApproximation subroutine has been implemented as outlined in Appendix E and Algorithm 5
2. **[7d2ca353]** (weight=1) The NystromPCGsubroutine has been implemented as outlined in Appendix E and Algorithm 6
3. **[080778c3]** (weight=1) The Armijo soubroutine has been implemented as outlined in Appendix E and Algorithm 7
4. **[3d63db7e]** (weight=1) NNCG has been implemented such that it follows the steps outlined in Algorithm 4 in Appendix E
5. **[3176afb0]** (weight=1) Code has been implemented such that training can be resumed using the gradient descent (GD) optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the convection problem domain
6. **[1172349c]** (weight=1) Code has been implemented such that training can be resumed using the gradient descent (GD) optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the reaction problem domain
7. **[e9d9db2b]** (weight=1) Code has been implemented such that training can be resumed using gradient descent (GD) optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the wave problem domain
8. **[62ba517c]** (weight=1) Code has been implemented such that training can be resumed using the NNCG optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the convection problem domain
9. **[3f8789ca]** (weight=1) Code has been implemented such that training can be resumed using the NNCG optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the reaction problem domain
10. **[97cf12cb]** (weight=1) Code has been implemented such that training can be resumed using the NNCG optimizer the Adam+L-BFGS configuration in the training sweep in section 2.2 with the lowest final L2RE for the wave problem domain
11. **[de05f797]** (weight=2) The recorded loss and gradient norms show that NNCG significantly improves both the loss and gradient norm of the solution when applied after Adam+L-BFGS across each successfully studied problem domain
12. **[a642fdcf]** (weight=2) The recorded loss and gradient norms show that GD improves neither the loss nor gradient norm of the solution when applied after Adam+L-BFGS across each successfully studied problem domain

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/pinn_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: pinn

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
