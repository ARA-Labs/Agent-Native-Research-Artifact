# Full Paper Reproduction: stochastic-interpolants

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/stochastic-interpolants_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/stochastic-interpolants_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/stochastic-interpolants.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/stochastic-interpolants` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/stochastic-interpolants_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Set up the U-Net velocity model architecture from lucidrains' denoising-diffusion-pytorch repository with the exact hyperparameters specified in the paper: dim=256, dim_mults=(1,1,2,3,4), learned_sinusoidal_cond=True, learned_sinusoidal_dim=32, attn_dim_head=64, attn_heads=4, random_fourier_features=False. Verify the model instantiates correctly and accepts the expected input tensor shapes (batch of images with variable channel counts for conditioning). [easy]

**Success criteria:**

1. **[fa71af11]** (weight=1) The U-Net architecture implementation from lucidrain's denoising-diffusion-pytorch repository is available
2. **[748d82fe]** (weight=5) The approximate velocity model is implemented as the U-net from the lucidrain's denoisingdiffusion-pytorch repository
3. **[ba327b00]** (weight=1) The U-net velocity model has the "dim_mults" argument set to (1, 1, 2, 3, 4) (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is (1, 2, 4, 8))
4. **[0bd8d434]** (weight=1) The U-net velocity model has the "dim" argument set to 256 (note there is no default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository for the dim argument)
5. **[9c00369e]** (weight=1) The U-net velocity model has the "learned_sinusoidal_cond" argument set to True (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is False)
6. **[33409f2f]** (weight=1) The U-net velocity model has the "learned_sinusoidal_dim" argument set to 32 (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is 16)
7. **[c4401ce0]** (weight=1) The U-net velocity model has the "attn_dim_head" hyperparameter set to 64 (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is 32)
8. **[f0329e30]** (weight=1) The U-net velocity model has the "attn_heads" hyperparameter set to 4 (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is 4)
9. **[eaf72173]** (weight=1) The U-net velocity model has the "random_fourier_features" hyperparameter set to False (note the default value for the Unet module from the lucidrain's denoisingdiffusion-pytorch repository is False)

### Subtask 2 of 10: Set up the shared training infrastructure and evaluation pipeline. Implement ImageNet data loading for train and validation splits. Configure the Adam optimizer (lr=2e-4, no weight decay), StepLR scheduler (gamma=0.99 every 1000 steps), gradient norm clipping at 10000, batch size 32, and 200k training steps. Set up the Dopri ODE solver from torchdiffeq for inference. Implement FID-50k computation using a standard Inception-v3 feature extractor. Verify the training loop runs for a small number of steps without errors. [easy]

**Success criteria:**

1. **[46ca1cd4]** (weight=1) Code for accessing the train and validation sets from the ImageNet dataset has been implemented
2. **[67af86d8]** (weight=1) A learning rate scheduler is used, which starts at a learning rate of 2e-4 and scaling the learning rate by $\gamma=0.99$ every $N=1000$ steps
3. **[cd04efc2]** (weight=1) Weight decay is not used
4. **[cb0f23e1]** (weight=1) Gradient norms are clipped at 10,000 (this is the norm of the entire set of parameters taken as a vector, the default type of norm clipping in PyTorch library)
5. **[ebc3e8cf]** (weight=1) The Dopri solver from the torchdiffeq library is used to solve the ODEs
6. **[7de84bdb]** (weight=1) All models are trained with a batch size of 32
7. **[7c7ebd70]** (weight=1) All models are trained for 200,000 gradient steps
8. **[190a2c3f]** (weight=1) The Frechet Inception Distance (FID) metric has been implemented

### Subtask 3 of 10: Implement the Uncoupled Interpolant training and sampling procedures for ImageNet inpainting (Section 4.1 baseline). Training: for each sample in a mini-batch, (1) sample x_0 ~ N(0,I), (2) add a class-conditioning channel uniformly filled with the class label, (3) sample t ~ U(0,1), (4) compute the interpolant I_t = t*x_0 + (1-t)*x_1, (5) compute the time-derivative dI_t = x_1 - x_0, (6) compute the quadratic velocity regression loss, and (7) train with Adam. Sampling: initialize X_0 ~ N(0,I), then iterate X_{i+1} = X_i + (1/N)*b_{i/N}(X_i) for N steps. Verify the full pipeline produces valid outputs. [easy]

**Success criteria:**

1. **[3f74c905]** (weight=2) During training the Uncoupled Interpolant model for in-painting, for each $i$-th sample in each mini-batch, the initial image is sampled as gaussian noise; $x_0 \sim \mathcal{N}(0, Id)$
2. **[f823b47a]** (weight=2) During training the Uncoupled Interpolant model for in-painting, for each $i$-th sample in each mini-batch, a channel is added which is uniformly filled with the sample's class value
3. **[d5402a39]** (weight=2) During training the Uncoupled Interpolant model for in-painting, for each $i$-th sample in each mini-batch, the time $t$ is uniformly sampled between 0 and 1, as $t_i \sim U(0, 1)$
4. **[3a9c64b6]** (weight=2) During training the Uncoupled Interpolant model for in-painting, for each $i$-th sample in a mini-batch, the interpolant $I_{t_i}$ is computed as $I_{t_i} = t x_0^i + (1-t) x_1^i$, where $x_0$ is the noisy image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
5. **[44d89bd8]** (weight=2) During training the Uncoupled Interpolant model for in-painting, for each $i$-th sample in a mini-batch, the time-derivative interpolant $\dot{I}_{t_i}$ is computed as $\dot{I}_{t_i} = x_1 - x_0$, where $x_0$ is the noisy image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
6. **[4730f7b6]** (weight=2) During training the Uncoupled Interpolant model for in-painting, the loss for a minibatch is computed as $\hat{L}_b(\hat{b}) = n_b^{-1} \sum_{i=1}^{n_b} \left[ |\hat{b}_{t_i}(I_{t_i})|^2 - 2\dot{I}_{t_i} \cdot \hat{b}_{t_i}(I_{t_i}) \right]$, where $n_b$ is the number of samples in the $i$-th minibatch, $\hat{b}_{t_i}$ is the approximate velocity field, $I_{t_i}$ is the interpolant, and $\dot{I}_{t_i}$ is the time-derivative interpolant
7. **[74e1ae29]** (weight=1) During training the Uncoupled Interpolant model for in-painting, the model is trained using the Adam optimizer
8. **[5afccb74]** (weight=1) During sampling with the Uncoupled Interpolant model for in-painting, the initial image is sampled as gaussian noise; $x_0 \sim \mathcal{N}(0, Id)$
9. **[e9d03723]** (weight=2) When sampling with the Uncoupled Interpolant model for in-painting, given $N \in \mathbb{N}$ total iterations, on the $i$-th iteration the sample $\hat{X}_{i+1}$ is computed as $\hat{X}_i + N^{-1}\hat{b}_{i/N}(\hat{X}_i)$, where $\hat{X}_0$ is the original gaussian noisy image, and $\hat{b}_{i/N}$ is the approximate velocity field at time $i/N$. The final result after $N$ iterations is the in-painted image

### Subtask 4 of 10: Implement the Euler-step sampling procedure for the Dependent Coupling super-resolution model (Algorithm 2 applied to super-resolution). At test time: (1) take a validation-set image, downsample to 64x64 by cropping, (2) upsample back to 256x256 via nearest-neighbor interpolation, (3) add Gaussian noise to form the corrupted initial image x_0, (4) append the upsampled low-res image along the channel dimension, (5) add a class-label channel, (6) iterate X_{i+1} = X_i + (1/N)*b_{i/N}(X_i) for N steps where the velocity field only updates the image channels. Verify the sampling pipeline produces valid 256x256 outputs from 64x64 inputs. [easy]

**Success criteria:**

1. **[9108d07c]** (weight=1) During sampling with the Dependent Coupling model for super-resolution, an image from the ImageNet validation or test set is sampled, then it is first downsampled by cropping to 64x64 if the original resolution was 256x256, or it is cropped to 256x256 if the original resolution was 512x512
2. **[52dab287]** (weight=1) During sampling with the Dependent Coupling model for super-resolution, nearest neighbour interpolation is applied to upsample the cropped image back to the original resolution
3. **[3a59ebee]** (weight=1) During sampling with the Dependent Coupling model for super-resolution, Gaussian noise is added to the downsampled and upsampled ImageNet image; $x_0 = \mathcal{U} ( \mathcal{D} (x_1)) + \zeta$, where $\zeta \sim \mathcal{N}(0, Id)$
4. **[9d2ac48f]** (weight=1) During sampling with the Dependent Coupling model for super-resolution, the image that has been downsampled, upsampled, and had gaussian noise added to it is appended to the original ImageNet image along the channel dimension to create the corrupted image
5. **[3c8fd9d0]** (weight=1) When sampling with the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, a channel is added which is uniformly filled with the sample's class value
6. **[547af5aa]** (weight=2) When sampling with the Dependent Coupling model for super-resolution, given $N \in \mathbb{N}$ total iterations, on the $i$-th iteration the sample $\hat{X}_{i+1}$ is computed as $\hat{X}_i + N^{-1}\hat{b}_{i/N}(\hat{X}_i)$, where $\hat{X}_0$ is the original corrupted image, and $\hat{b}_{i/N}$ is the approximate velocity field at time $i/N$. The final result after $N$ iterations is the image at a higher resolution

### Subtask 5 of 10: Implement the Euler-step sampling procedure (Algorithm 2) for the Dependent Coupling inpainting model. Construct the masked initial image x_0 = xi*x_1 + (1-xi)*zeta using the tile-mask scheme (64 tiles, p=0.3, channel-shared mask taking the same value across channels at each spatial location), where x_1 is from the ImageNet validation set. Add the class-conditioning channel, then iterate X_{i+1} = X_i + (1/N)*b_{i/N}(X_i) for N steps. Verify the sampling pipeline produces valid 256x256 inpainted images with known pixels preserved. [medium]

**Success criteria:**

1. **[4b3e6602]** (weight=1) During sampling with the Dependent Coupling model for in-painting, the mask is drawn randomly by tiling the image into 64 tiles of equal sizes; each tile is selected to enter the mask with probability $p = 0.3$
2. **[c6ba9100]** (weight=1) During sampling with the Dependent Coupling model for in-painting, the mask that is computed takes the same value for all channels in a given spatial location
3. **[d9883334]** (weight=1) During sampling with the Dependent Coupling model for in-painting, the mask is applied to the input image such that masked regions contain random noise, computed as $x_0 = \xi \circ x_1 + (1-\xi) \circ \zeta$, where $\circ$ denotes the Hadamard (elementwise) product, and the random noise $\zeta \in \mathbb{R}^{C \times W \times H}, \zeta \sim N(0, Id)$ is used to initialize the pixels within the masked region (separate noise is used for each channel), and $\xi$ denotes the mask. This input image is from the ImageNet validation or test set
4. **[3fd598f3]** (weight=1) When sampling with the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, a channel is added which is uniformly filled with the sample's class value
5. **[35183fae]** (weight=2) When sampling with the Dependent Coupling model for in-painting, given $N \in \mathbb{N}$ total iterations, on the $i$-th iteration the sample $\hat{X}_{i+1}$ is computed as $\hat{X}_i + N^{-1}\hat{b}_{i/N}(\hat{X}_i)$, where $\hat{X}_0$ is the original masked image, and $\hat{b}_{i/N}$ is the approximate velocity field at time $i/N$. The final result after $N$ iterations is the in-painted image

### Subtask 6 of 10: Implement the data preparation pipeline for the Dependent Coupling super-resolution training (Section 4.2). For each sample: (1) downsample the 256x256 ImageNet image to 64x64 by cropping, (2) upsample back to 256x256 via nearest-neighbor interpolation, (3) add Gaussian noise x_0 = U(D(x_1)) + zeta where zeta ~ N(0,I), (4) append the upsampled low-res image along the channel dimension as conditioning input, (5) add a class-label channel. Verify the corrupted image has the correct shape and the low-frequency structure is preserved in the conditioning channel. [medium]

**Success criteria:**

1. **[74ebafd7]** (weight=1) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, an image from the ImageNet training set is first downsampled by cropping to 64x64 if the original resolution was 256x256, or it is cropped to 256x256 if the original resolution was 512x512
2. **[af9c0ad4]** (weight=1) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, nearest neighbour interpolation is applied to upsample the cropped image back to the original resolution
3. **[f701ec5c]** (weight=1) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, Gaussian noise is added to the downsampled and upsampled ImageNet image; $x_0 = \mathcal{U} ( \mathcal{D} (x_1)) + \zeta$, where $\zeta \sim \mathcal{N}(0, Id)$, $\mathcal{U}$ is the upsampling operation, and $\mathcal{D}$ is the downsampling operation
4. **[36ae2f00]** (weight=1) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, the image that has been downsampled, upsampled, and had gaussian noise added to it is appended to the original ImageNet image along the channel dimension to create the corrupted image
5. **[f118676d]** (weight=2) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, a channel is added which is uniformly filled with the sample's class value

### Subtask 7 of 10: Implement the Dependent Coupling training loop for ImageNet super-resolution (Section 4.2). Given the prepared corrupted images from T07, for each sample: (1) sample t ~ U(0,1), (2) compute the interpolant I_t = t*x_0 + (1-t)*x_1 where x_0 is the corrupted image and x_1 is the original, (3) compute the time-derivative dI_t = x_1 - x_0, (4) ensure the velocity field only acts on the interpolant image channels (not the appended low-resolution conditioning or class channels), (5) compute the quadratic velocity regression loss, and (6) train with Adam. Verify training loss converges on a small subset of ImageNet. [medium]

**Success criteria:**

1. **[d790efdd]** (weight=2) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in each mini-batch, the time $t$ is uniformly sampled between 0 and 1, as $t_i \sim U(0, 1)$
2. **[6b23bcf6]** (weight=2) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in a mini-batch, the interpolant $I_{t_i}$ is computed as $I_{t_i} = t x_0^i + (1-t) x_1^i$, where $x_0$ is the corrupted image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
3. **[5aa12bc7]** (weight=2) During training the Dependent Coupling model for super-resolution, for each $i$-th sample in a mini-batch, the time-derivative interpolant $\dot{I}_{t_i}$ is computed as $\dot{I}_{t_i} = x_1 - x_0$, where $x_0$ is the corrupted image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
4. **[b3d613a2]** (weight=2) During training the Dependent Coupling model for super-resolution, the velocity field only acts on the interpolant image, not the additional class channel that has been appended, or the low-resolution image that has been appended
5. **[ff8dbe4e]** (weight=2) During training the Dependent Coupling model for super-resolution, the loss for a minibatch is computed as $\hat{L}_b(\hat{b}) = n_b^{-1} \sum_{i=1}^{n_b} \left[ |\hat{b}_{t_i}(I_{t_i})|^2 - 2\dot{I}_{t_i} \cdot \hat{b}_{t_i}(I_{t_i}) \right]$, where $n_b$ is the number of samples in the $i$-th minibatch, $\hat{b}_{t_i}$ is the approximate velocity field, $I_{t_i}$ is the interpolant, and $\dot{I}_{t_i}$ is the time-derivative interpolant
6. **[75958462]** (weight=1) During training the Dependent Coupling model for super-resolution, the model is trained using the Adam optimizer

### Subtask 8 of 10: Implement the Dependent Coupling training procedure for ImageNet inpainting (Section 4.1). For each sample in a mini-batch: (1) draw a random binary tile mask by dividing the image into 64 tiles, each selected with probability p=0.3, shared across channels, (2) construct the masked image x_0 = xi*x_1 + (1-xi)*zeta where zeta ~ N(0,I), (3) add a class-conditioning channel, (4) sample t ~ U(0,1), (5) compute I_t = t*x_0 + (1-t)*x_1 and dI_t = x_1 - x_0, (6) mask the velocity field output to zero in unmasked regions, (7) compute the quadratic loss, and (8) train with Adam. [hard]

**Success criteria:**

1. **[e04c1c97]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, the mask is drawn randomly by tiling the image into 64 tiles of equal sizes; each tile is selected to enter the mask with probability $p = 0.3$
2. **[036df75d]** (weight=1) During training the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, the mask that is computed takes the same value for all channels in a given spatial location
3. **[551ad22d]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, the mask is applied to an image from the ImageNet training set such that masked regions contain random noise, computed as $x_0 = \xi \circ x_1 + (1-\xi) \circ \zeta$, where $\circ$ denotes the Hadamard (elementwise) product, and the random noise $\zeta \in \mathbb{R}^{C \times W \times H}, \zeta \sim N(0, Id)$ is used to initialize the pixels within the masked region (separate noise is used for each channel), and $\xi$ denotes the mask
4. **[75cc97d2]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, a channel is added which is uniformly filled with the sample's class value
5. **[ee1e4da3]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in each mini-batch, the time $t$ is uniformly sampled between 0 and 1, as $t_i \sim U(0, 1)$
6. **[8c2b4e77]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in a mini-batch, the interpolant $I_{t_i}$ is computed as $I_{t_i} = t x_0^i + (1-t) x_1^i$, where $x_0$ is the masked image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
7. **[2326b8d4]** (weight=2) During training the Dependent Coupling model for in-painting, for each $i$-th sample in a mini-batch, the time-derivative interpolant $\dot{I}_{t_i}$ is computed as $\dot{I}_{t_i} = x_1 - x_0$, where $x_0$ is the masked image, $x_1$ is the original ImageNet image, and $t$ is the sampled time
8. **[718205ed]** (weight=2) During training the Dependent Coupling model for in-painting, the approximate velocity field $b_t(x, \xi)$ is defined such that $b_t(x, \xi) = 0$ except in the masked regions of the image; the output of the approximate velocity field is masked to enforce that the unmasked pixels remain fixed. Here, $x$ denotes some image and $\xi$ denotes the conditioning variable. The approximate velocity field only acts on the image, not the additional class channel that has been appended
9. **[cbe7cd9e]** (weight=2) During training the Dependent Coupling model for in-painting, the loss for a minibatch is computed as $\hat{L}_b(\hat{b}) = n_b^{-1} \sum_{i=1}^{n_b} \left[ |\hat{b}_{t_i}(I_{t_i})|^2 - 2\dot{I}_{t_i} \cdot \hat{b}_{t_i}(I_{t_i}) \right]$, where $n_b$ is the number of samples in the $i$-th minibatch, $\hat{b}_{t_i}$ is the approximate velocity field, $I_{t_i}$ is the interpolant, and $\dot{I}_{t_i}$ is the time-derivative interpolant
10. **[8190541a]** (weight=1) During training the Dependent Coupling model for in-painting, the model is trained using the Adam optimizer

### Subtask 9 of 10: Train both the Uncoupled Interpolant and Dependent Coupling inpainting models on ImageNet for 50k gradient steps each (25% of full budget, 1 seed). Generate 50k inpainted samples from each model using the Euler sampler and compute FID-50k on the ImageNet validation set for both. Verify the Uncoupled Interpolant achieves FID-50k in the neighborhood of 1.35 and the Dependent Coupling model achieves FID-50k in the neighborhood of 1.15, confirming that dependent coupling strictly improves over the independent baseline. [hard]

**Success criteria:**

1. **[1fb894bd]** (weight=1) The Uncoupled Interpolant model is trained on ImageNet
2. **[948edecc]** (weight=1) Using the Uncoupled Interpolant model that has been trained on ImageNet, FID-50k is computed on the ImageNet validation set
3. **[499e91ba]** (weight=1) The Uncoupled Interpolant model achieves FID-50k around 1.35
4. **[2933a4be]** (weight=1) The Dependent Coupling model is trained on ImageNet
5. **[9edcca4e]** (weight=1) Using the Dependent Coupling model that has been trained on ImageNet, FID-50k is computed on the ImageNet validation set
6. **[79043fe8]** (weight=1) The Dependent Coupling model achieves FID-50k around 1.15

### Subtask 10 of 10: Train the Dependent Coupling super-resolution model on ImageNet for 50k gradient steps (25% of full budget, 1 seed). Generate 50k super-resolved samples (64x64 to 256x256) and compute FID-50k on both the ImageNet training set (vs. 50k random training images) and the ImageNet validation set. Verify the model achieves train FID-50k in the neighborhood of 2.15 and validation FID-50k in the neighborhood of 2.05, demonstrating competitive performance against published baselines (Improved DDPM, SR3, ADM, Cascaded Diffusion, I2SB) from Table 3. [hard]

**Success criteria:**

1. **[04e0713d]** (weight=1) The Dependent Coupling model is trained on ImageNet
2. **[07327a66]** (weight=1) Using the Dependent Coupling model that has been trained on ImageNet, FID-50k is computed on the ImageNet train set by comparing against 50k random samples from the training set
3. **[58ed3cb6]** (weight=1) Using the Dependent Coupling model that has been trained on ImageNet, FID-50k is computed on the ImageNet validation set
4. **[4d62ee04]** (weight=1) The Dependent Coupling model achieves train FID-50k around 2.15 for the super-resolution task
5. **[33e2261e]** (weight=1) The Dependent Coupling model achieves validation FID-50k around 2.05 for the super-resolution task

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/stochastic-interpolants_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: stochastic-interpolants

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
