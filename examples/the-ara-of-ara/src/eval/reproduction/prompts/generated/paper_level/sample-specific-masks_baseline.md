# Full Paper Reproduction: sample-specific-masks

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sample-specific-masks_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sample-specific-masks_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/sample-specific-masks.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/sample-specific-masks` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sample-specific-masks_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the iterative label mapping (ILM) module following Chen et al. (2023) and the Pad baseline for visual reprogramming. ILM must correctly compute frequency distributions and derive the output mapping each epoch. The Pad baseline must initialize a learnable noise pattern, center the input image, concatenate the pattern around it, feed through the frozen pre-trained model, apply ILM, compute cross-entropy loss, and update only the noise pattern via gradient descent. Verify correctness with ResNet-18 on CIFAR10 and OxfordPets using the correct hyperparameters (LR=0.01, decay=0.1 at epochs 100/145, 200 epochs, batch 256 for CIFAR10, batch 64 for OxfordPets). [easy]

**Success criteria:**

1. **[3982c682]** (weight=1) Code for making ResNet-18, pre-trained on ImageNet-1K, available for further training and evaluation has been implemented
2. **[f84d16cb]** (weight=1) Code for accessing the train and test splits from the CIFAR10 dataset has been implemented
3. **[f45b8463]** (weight=1) Code for accessing the train and test splits from the OxfordPets dataset has been implemented
4. **[2a23ed70]** (weight=1) When computing the frequency distribution of the dataset, a matrix $d$ is initialized with zeros; $d \leftarrow \{0\}^{|\mathcal{Y}^P| \times |\mathcal{Y}^T|}$, where $\mathcal{Y}^T$ are the labels of the target task, and $\mathcal{Y}^P$ are the labels of the pre-trained task
5. **[04ab5a91]** (weight=1) When computing the frequency distribution of the dataset, given a target training set $\{(x_i^T,y_i^T)\}_{i=1}^n$, for each sample in the training set, the output label is computed as $\hat{y}_i^P \leftarrow f_P\left(f_\text{in}\left(x_i^\top \vert \theta \right)\right)$, where $f_P$ is the pre-trained model, and $f_{\text{in}}(\cdot | \theta)$ is the visual reprogramming model
6. **[e72bdc32]** (weight=1) When computing the frequency distribution of the dataset, for each predicted label $\hat{y}_i^P$, the frequency distribution matrix is updated; $d_{\hat{y}_i^P, y_i^T} \leftarrow d_{\hat{y}_i^P, y_i^T} + 1$
7. **[1aa39331]** (weight=1) When computing the output mapping using Iterative label mapping, at the start of each epoch the frequency distribution of the target training set is first computed
8. **[2da66162]** (weight=2) When computing the output mapping using Iterative label mapping, on each epoch the following algorithm is applied; $\mathcal{Y}_\text{sub}^P$ is initialized as $\emptyset$. Until the size of $\mathcal{Y}_\text{sub}^P$ is $|\mathcal{Y}^T|$ the following steps are taken: 1) the maximum $d_{y^P, y^T}$ in frequency distribution $d$ is found and added to $\mathcal{Y}_\text{sub}^P$, 2) the label mapping is updated as $f_\text{out}^\text{Ilm} (y^P) \leftarrow y^T$, 3) the frequency distribution is updated as $d_{y^P, t} \leftarrow 0 \text{ for } t=1,2,...,|\mathcal{Y}^T|$, and $d_{s, y^T} \leftarrow 0 \text{ for } s=1,2,...,|\mathcal{Y}^P|$
9. **[1659bb57]** (weight=1) For the Pad baseline, a pattern is initialized, with shape equivalent to the expected input shape of the pre-trained model
10. **[d41661a4]** (weight=1) For the Pad baseline, the input image is centered, then the noise pattern is concatenated around the image to form the expected input shape for the pre-trained model (only if the input image is smaller than the required input size for the pre-trained model)
11. **[09a272e5]** (weight=1) For the Pad baseline, the input image (that has the masked pattern concatenated around it) is fed into the pretrained model
12. **[a7cee3c7]** (weight=1) For the Pad baseline, the predicted label from the pre-trained model is mapped using the iterative label mapping (ILM)
13. **[2f60699e]** (weight=1) For the Pad baseline, cross-entropy loss is computed between the predicted labels and the target labels
14. **[49822754]** (weight=1) For the Pad baseline, only the noise pattern is updated through gradient descent

### Subtask 2 of 10: Implement the three remaining shared-mask watermarking baselines: Narrow (28-pixel edge mask), Medium (quarter-size center mask), and Full (full watermark). Each method must initialize a learnable noise pattern, define its mask shape, resize input images via bilinear interpolation, apply the masked pattern, pass through the pre-trained model with ILM, compute cross-entropy loss, and update only the noise pattern. Configure correct hyperparameters for all baselines (LR=0.01, decay=0.1 at epochs 100/145, 200 epochs, batch sizes 256/64). [easy]

**Success criteria:**

1. **[82aec253]** (weight=1) For the Narrow baseline, a pattern is initialized, with shape equivalent to the expected input shape of the pre-trained model
2. **[7b29d3dc]** (weight=1) For the Narrow baseline, a mask is defined with shape equivalent to the expected input shape to the pre-trained model. All values are masked aside from the edges of the image, with this edge having width 28
3. **[029e1a82]** (weight=1) For the Narrow baseline, each input image is resized using bilinear interpolation to match the expected size of the pre-trained model
4. **[c3885380]** (weight=1) For the Narrow baseline, the pattern is added to the input image only where the mask permits
5. **[3010baa0]** (weight=1) For the Narrow baseline, the input image (that has the masked pattern added to it) is fed into the pretrained model
6. **[727cea73]** (weight=1) For the Narrow baseline, the predicted label from the pre-trained model is mapped using the iterative label mapping (ILM)
7. **[5760dac1]** (weight=1) For the Narrow baseline, cross-entropy loss is computed between the predicted labels and the target labels
8. **[3d9bfc0b]** (weight=1) For the Narrow baseline, only the noise pattern is updated through gradient descent
9. **[c2bd1ec0]** (weight=1) For the Medium baseline, a pattern is initialized, with shape equivalent to the expected input shape of the pre-trained model
10. **[a354fa2f]** (weight=1) For the Medium baseline, a mask is defined with shape equivalent to the expected input shape to the pre-trained model. All values are masked, aside from a central shape being a quarter of the size of the height and width of the expected input shape to the pre-trained model
11. **[07faea63]** (weight=1) For the Medium baseline, each input image is resized using bilinear interpolation to match the expected size of the pre-trained model
12. **[011c0d8d]** (weight=1) For the Medium baseline, the pattern is added to the input image only where the mask permits
13. **[e1b7d56c]** (weight=1) The Pad, Narrow, Medium and Full baselines are trained with an initial learning rate of 0.01
14. **[c19f72e5]** (weight=1) The Pad, Narrow, Medium and Full baselines are trained with a learning rate decay of 0.1, which is applied on the 100th and 145th epochs
15. **[23394dfb]** (weight=1) The Pad, Narrow, Medium and Full baselines are trained for two hundred epochs

### Subtask 3 of 10: Implement the SMM (Sample-specific Mask) method for ResNet-18/50. This includes: (1) the 5-layer CNN mask generator with correct channel progression (3->8->16->32->64->3), BatchNorm, ReLU, and MaxPool as specified; (2) the patch-wise interpolation module that upscales low-resolution masks to full resolution; (3) the end-to-end training loop following Algorithm 1: initialize delta to zeros and mask generator randomly, generate per-sample masks, apply patch-wise interpolation, compute f_in(x) = r(x) + delta * f_mask(r(x)), pass through frozen pre-trained model with ILM, and update both delta and mask generator via SGD. [easy]

**Success criteria:**

1. **[fe4f42fb]** (weight=1) For SSM, each input image is resized using bilinear interpolation to match the expected size of the mask generator
2. **[28be07ce]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the mask generator is a 5-layer CNN
3. **[c4ae713d]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the first layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 8 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
4. **[02c368c6]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the second layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 16 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
5. **[b3bb8a27]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the third layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 32 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
6. **[adad65b3]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the fourth layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 64 output channels, followed by BatchNorm, then ReLU
7. **[a3709fb5]** (weight=1) When using the SSM method with ResNet-18 or ResNet-50, the fifth layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 3 output channels
8. **[43b56ae9]** (weight=1) In the mask generator module in SSM, given a three-channel image as input with height $H$ and width $W$, the mask generator outputs a three-channel mask with dimensions $\left\lfloor \frac{H}{2^l} \right\rfloor \times \left\lfloor \frac{W}{2^l} \right\rfloor$, where $l$ denotes the number of pooling layers in the mask generator CNN
9. **[0315e7cf]** (weight=1) In the Patch-wise Interpolation Module in SSM, if the number of pooling layers in the mask generator CNN is not zero, each pixel is enlarged to $2^l \times 2^l$ pixels using bilinear interpolation. If this expansion does not evenly cover the image area (e.g. near the image edges) the value of the nearest available pixel is used to fill in any gaps.
10. **[1148dc53]** (weight=1) In the Patch-wise Interpolation Module in SSM, if the number of pooling layers in the mask generator CNN is zero, then the input image is not enlarged
11. **[613293bb]** (weight=1) When training a model using the SSM method, the parameters of the CNN mask generator are initialized randomly
12. **[d032889a]** (weight=1) When training a model using the SSM method, the pattern $\delta$ is initialized to zeros
13. **[0fde2a77]** (weight=1) When training a model using the SSM method, individual masks for each image in the training batch are generated by the mask generator
14. **[0cea4c76]** (weight=1) When training a model using the SSM method, the generated masks for each image in each training batch are resized using the patch-wise interpolation module
15. **[27c360ce]** (weight=1) When training a model using the SSM method, for each image in the batch, the pattern $\delta$ is multiplied with the mask on a pixel-wise basis and added to the resized input image (which has just resized using the patch-wise interpolation module)

### Subtask 4 of 10: Train and evaluate both the Pad baseline and SMM (Ours) using ResNet-18 on CIFAR10 and SVHN (3 seeds each). Use correct hyperparameters (LR=0.01, decay=0.1 at epochs 100/145, batch=256, 200 epochs, patch size=8 for SMM). Record mean and std of test accuracy. Verify that SMM outperforms Pad on both datasets, and that SMM achieves roughly [X]% absolute improvement over Pad on SVHN for ResNet-18. [medium]

**Success criteria:**

1. **[08e02fff]** (weight=1) Code for accessing the train and test splits from the SVHN dataset has been implemented
2. **[87b4dcc3]** (weight=1) All ResNet models trained on any of the CIFAR10, CIFAR100, SVHN, GTSRB, FLOWERS102, UCF101, FOOD101, SUN397, EUROSAT datasets use a batch size of 256, initial learning rate of 0.01 and learning-rate decay of 0.1
3. **[0e394886]** (weight=1) The Pad, Narrow, Medium and Full baselines trained on any of the CIFAR10, CIFAR100, SVHN, GTSRB, FLOWERS102, UCF101, FOOD101, SUN397, EUROSAT datasets use a batch size of 256
4. **[a27fe007]** (weight=1) Unless otherwise stated, the patch size for SSM is set to $2^l$ where $l$ is the number of max-pooling layers
5. **[913baecd]** (weight=1) When training models with the SSM method, if a learning rate decay that isn't 1 is used, the learning rate scheduler applies the decay factor on the 100th and 145th epochs
6. **[29ccdd70]** (weight=1) Using the "Pad" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
7. **[cc6cc6c8]** (weight=1) Using the "Pad" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
8. **[4e8a2662]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
9. **[8d6e26aa]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
10. **[28aade60]** (weight=1) The recorded metrics show that SMM roughly has a 6% (absolute) improvement over the next best input reprogramming method when using ResNet-18 on the SVHN dataset

### Subtask 5 of 10: Train and evaluate all five methods (Pad, Narrow, Medium, Full, SMM) using ResNet-18 on Flowers102 and EuroSAT (3 seeds each, batch=256). Record mean and std of test accuracy. Verify that SMM achieves the highest accuracy on both datasets, with roughly [X]% absolute improvement over the best baseline on Flowers102 and roughly 10% on EuroSAT for ResNet-18. [medium]

**Success criteria:**

1. **[bfed30a3]** (weight=1) Code for accessing the train and test splits from the Flowers102 dataset has been implemented
2. **[4c9b219d]** (weight=1) Code for accessing the train and test splits from the EuroSAT dataset has been implemented
3. **[55186fba]** (weight=1) Using the "Pad" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
4. **[5eff8822]** (weight=1) Using the "Pad" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
5. **[0b93529d]** (weight=1) Using the "Narrow" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
6. **[5e68176b]** (weight=1) Using the "Narrow" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
7. **[5f73fbf7]** (weight=1) Using the "Medium" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
8. **[5b3bc88a]** (weight=1) Using the "Medium" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
9. **[e59d6acb]** (weight=1) Using the "Full" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
10. **[a73f93c3]** (weight=1) Using the "Full" reprogramming method, ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
11. **[bc63b917]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
12. **[6b00f1df]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
13. **[e3db8d69]** (weight=1) The recorded metrics show that SMM roughly has a 10% (absolute) improvement over the next best input reprogramming method when using ResNet-18 on the Flowers102 dataset
14. **[36b3e62b]** (weight=1) The recorded metrics show that SMM roughly has a 10% (absolute) improvement over the next best input reprogramming method when using ResNet-50 on the Flowers102 dataset

### Subtask 6 of 10: Train and evaluate both the Pad baseline and SMM using ResNet-50 on CIFAR10 and Flowers102 (3 seeds each, correct hyperparameters). Record mean and std of test accuracy. Verify that SMM achieves the highest average accuracy across all datasets when using ResNet-50, confirming that SMM's advantage generalizes from ResNet-18 to ResNet-50. [medium]

**Success criteria:**

1. **[57d7b55b]** (weight=1) Code for making ResNet-50, pre-trained on ImageNet-1K, available for further training and evaluation has been implemented
2. **[2ac32251]** (weight=1) All ResNet models trained on either the DTD or OXFORDPETS dataset use a batch size of 64, initial learning rate of 0.01 and learning-rate decay of 0.1
3. **[83f678ea]** (weight=1) Using the "Pad" reprogramming method, ResNet-50 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
4. **[e9a1a7b1]** (weight=1) Using the "Pad" reprogramming method, ResNet-50 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
5. **[6c15c084]** (weight=1) Using the SNS method ("Ours"), ResNet-50 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
6. **[6e482102]** (weight=1) Using the SNS method ("Ours"), ResNet-50 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
7. **[1415e5b0]** (weight=1) The recorded metrics show that SMM yields higher accuracy compared to all other input reprogramming methods for ResNet-50 on almost all (or all) datasets
8. **[7a6194fb]** (weight=1) The recorded metrics show that SMM has the highest average accuracy across all datasets when using ResNet-50

### Subtask 7 of 10: Compute ResNet-18 penultimate-layer embeddings for 5000 randomly selected training samples from SVHN and EuroSAT under three conditions: (1) no VR (raw ResNet-18), (2) Full watermarking, and (3) SMM. Apply t-SNE to project embeddings to 2D. Verify that raw ResNet-18 embeddings show poor class separation, that Full watermarking improves separation somewhat, and that SMM produces the best class separation among all methods. [medium]

**Success criteria:**

1. **[78ac48cc]** (weight=1) 5000 samples are (separately) randomly selected from the training sets of the SVHN and EuroSAT datasets
2. **[dcc68c79]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using ResNet-18
3. **[9e037051]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using the "Pad" reprogramming method, with ResNet-18 as the pre-trained model
4. **[ca6af6fc]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using the "Narrow" reprogramming method, with ResNet-18 as the pre-trained model
5. **[5691f99a]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using the "Medium" reprogramming method, with ResNet-18 as the pre-trained model
6. **[6f88164d]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using the "Full" reprogramming method, with ResNet-18 as the pre-trained model
7. **[a8339d1b]** (weight=1) The embeddings of the randomly selected samples in the training sets of the SVHN and EuroSAT datasets are computed using the SMM ("Ours") reprogramming method, with ResNet-18 as the pre-trained model
8. **[9d2a4385]** (weight=1) tSNE is applied to the embeddings to project the embeddings to 2 dimensions
9. **[237676cb]** (weight=1) The recorded metrics show that before applying any VR methods (i.e. just looking at ResNet-18 embeddings), the output feature space has limited class separation
10. **[5f41a380]** (weight=1) The recorded metrics show that the "Ours" method has the best class separation in output feature space compared to other baseline methods, across both datasets

### Subtask 8 of 10: Implement the 6-layer CNN mask generator for ViT-B32 (channels 3->8->16->32->64->128->3 with 4 pooling layers), configure ViT-specific hyperparameters (LR=0.001, decay=1, images resized to 384x384), and train all five methods (Pad, Narrow, Medium, Full, SMM) on Flowers102 and Food101 with ViT-B32 (3 seeds each). Verify that SMM achieves roughly [X]% absolute improvement over the best baseline on Flowers102 and roughly [X]% on Food101. [hard]

**Success criteria:**

1. **[6c6b1ad5]** (weight=1) Code for making ViT-B32, pre-trained on ImageNet-1K, available for further training and evaluation has been implemented
2. **[50319077]** (weight=1) When using the SSM method with ViT-B32, the mask generator is a 6-layer CNN
3. **[59ff8add]** (weight=1) When using the SSM method with ViT-B32, the first layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 8 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
4. **[33204cda]** (weight=1) When using the SSM method with ViT-B32, the second layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 16 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
5. **[5fc09bcb]** (weight=1) When using the SSM method with ViT-B32, the third layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 32 output channels, followed by BatchNorm, ReLU, then a 2*2 Max Pool
6. **[c43bdbe6]** (weight=1) When using the SSM method with ViT-B32, the fourth layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 64 output channels, followed by BatchNorm, then ReLU
7. **[7719f69d]** (weight=1) When using the SSM method with ViT-B32, the fifth layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 128 output channels, followed by BatchNorm, then ReLU
8. **[a03cef9e]** (weight=1) When using the SSM method with ViT-B32, the sixth layer of the mask generator is a 3*3 convolution of padding size 1 and stride 1 with 3 output channels
9. **[7799ad6e]** (weight=1) All ViT models trained on any of the CIFAR10, CIFAR100, SVHN, GTSRB, FLOWERS102, UCF101, FOOD101, SUN397, EUROSAT datasets use a batch size of 256, initial learning rate of 0.001 and learning-rate decay of 1
10. **[1055ba97]** (weight=1) Using the SNS method ("Ours"), ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
11. **[43767618]** (weight=1) Using the SNS method ("Ours"), ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the FOOD101 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
12. **[80b9098e]** (weight=1) The recorded metrics show that SMM achieves roughly a [X]% (absolute) improvement over the next best input reprogramming method for ViT on the Flowers102 dataset
13. **[688a2c83]** (weight=1) The recorded metrics show that SMM achieves roughly a [X]% (absolute) improvement over the next best input reprogramming method for ViT on the Food101 dataset

### Subtask 9 of 10: Implement and train the three ablated SMM variants on ViT-B32: (1) Only-delta (shared-pattern VR, no mask generator), (2) Only-fmask (sample-specific pattern without shared delta), (3) Single-channel fmask^s (average penultimate-layer output). Train each variant on CIFAR10 and Flowers102 with ViT-B32 (3 seeds each). Verify that full three-channel SMM achieves the best average accuracy, that Only-fmask underperforms on data-abundant datasets, and that single-channel SMM underperforms on Flowers102. [hard]

**Success criteria:**

1. **[4ab4e8e2]** (weight=1) The Shared-pattern VR variant (aka. "only $\delta$") is implemented by defining visual reprogramming as $f_\text{in}(x_i)=r(x_i)+\delta$, where $r$ is bilinear interpolation, i.e., no masking is used
2. **[b525d390]** (weight=1) The sample-specific pattern without masking variant (aka. "only $f_{mask}$") is implemented by defining visual reprogramming as $f_\text{in}(x_i)=r(x_i)+f_\text{mask}(r(x_i))$ where $r$ is bilinear interpolation, i.e., no pattern is used
3. **[647e8cc8]** (weight=1) The Single-channel version of SMM variant (aka. "Single-Channel $f_\text{mask}^s$") is implemented by implementing VR as $f_\text{in}(x_i)=r(x_i)+\delta \odot f_\text{mask}(r(x_i))$, i.e., a single-channel version of SMM is used, averaging the penultimate-layer output of the mask generator
4. **[bb1e2cb0]** (weight=1) Using the "Shared-pattern VR variant" SMM variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
5. **[76919e09]** (weight=1) Using the "Shared-pattern VR variant" SMM variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the GTSRB dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
6. **[ded7a725]** (weight=1) Using the "sample-specific pattern without masking" SMM variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
7. **[58fa0ebb]** (weight=1) Using the "sample-specific pattern without masking" SMM variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the GTSRB dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
8. **[645fe9c1]** (weight=1) Using the "The Single-channel version of SMM" variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the CIFAR10 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
9. **[c7adc31d]** (weight=1) Using the "The Single-channel version of SMM" variant, ViT-B32 (pre-trained on ImageNet-1K) has been fine-tuned on the train split of the GTSRB dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
10. **[f516bb4c]** (weight=1) The recorded metrics show that the default SMM ("Ours") method achieves the best average accuracy for each dataset across all mask variants for ViT
11. **[105c14cc]** (weight=1) The recorded metrics show that the Sample-specific pattern without masking variant (aka. "Only $f_\text{mask}$") achieves the lowest average accuracy for ViT for the CIFAR10, SVHN, GTSRB, and SUN397 datasets
12. **[251d1112]** (weight=1) The recorded metrics show that the Single-channel version of SMM variant (aka. "Single-Chanel $f_\text{mask}^s$") performs significantly worse (at least 5%) than the default SMM ("Ours") method for ViT for the GTSRB and Flowers102 datasets

### Subtask 10 of 10: Train SMM with ResNet-18 using four patch sizes (1, 2, 4, 16 corresponding to 0, 1, 2, 4 pooling layers in the mask generator) on EuroSAT and Flowers102 (3 seeds each). Verify that patch size 4 outperforms patch size 1 on both datasets, and that patch size 16 performs similarly to the default patch size 8, confirming that SMM accuracy is robust to the patch size hyperparameter. [hard]

**Success criteria:**

1. **[336893af]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 1 (i.e. the mask generator has zero max-pooling layers) has been fine-tuned on the train split of the CIFAR100 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
2. **[b016a53e]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 1 (i.e. the mask generator has zero max-pooling layers) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
3. **[75c8bfe3]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 1 (i.e. the mask generator has zero max-pooling layers) has been fine-tuned on the train split of the FLOWERS102 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
4. **[f426b856]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 1 (i.e. the mask generator has zero max-pooling layers) has been fine-tuned on the train split of the EUROSAT dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
5. **[d4753360]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 2 (i.e. the mask generator has one max-pooling layer) has been fine-tuned on the train split of the CIFAR100 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
6. **[1090e6b8]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 2 (i.e. the mask generator has one max-pooling layer) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
7. **[476f144c]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 4 (i.e. the mask generator has two max-pooling layers) has been fine-tuned on the train split of the CIFAR100 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
8. **[513d9f00]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 4 (i.e. the mask generator has two max-pooling layers) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
9. **[ee7c7b65]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 16 (i.e. the mask generator has four max-pooling layers) has been fine-tuned on the train split of the CIFAR100 dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
10. **[6b2a337f]** (weight=1) Using the SNS method ("Ours"), ResNet-18 (pre-trained on ImageNet-1K) with patch size 16 (i.e. the mask generator has four max-pooling layers) has been fine-tuned on the train split of the SVHN dataset, then the accuracy at the end of training on the test split is recorded. This is repeated three times with three unique seeds, and the mean and standard deviation of the test accuracy is computed
11. **[4087ac21]** (weight=1) The recorded metrics show that the accuracy of the SMM with patch size 4 is greater than the accuracy of SMM with patch size 1. This result holds for all datasets CIFAR100, FLOWERS102, SVHN, and EUROSAT
12. **[e18ae43e]** (weight=1) The recorded metrics show that the accuracy of the SMM with patch size 16 is similar the accuracy of SMM with patch size 4, i.e., the difference is smaller than the difference when comparing patch size 4 to patch size 1. This result holds for all datasets CIFAR100, FLOWERS102, SVHN, and EUROSAT

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/sample-specific-masks_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: sample-specific-masks

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
