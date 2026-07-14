# Full Paper Reproduction: mechanistic-understanding

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/mechanistic-understanding_ara_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/mechanistic-understanding_ara_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the paper's **structured research artifact (ARA)**. You have NO access to the original paper PDF or its companion GitHub repository.

**ARA artifact location**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/artifacts/mechanistic-understanding`

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

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/mechanistic-understanding_ara_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement a linear toxicity probe on GPT2-medium and train it on the Jigsaw toxic comment classification dataset. Split the Jigsaw dataset into 90:10 train/validation sets. Implement a binary classifier of the form softmax(Wx) where x is the last-layer residual stream averaged across all timesteps and W has dimensionality Kx2 (one column for non-toxic, one for toxic). Train the probe on the training split, evaluate on the validation split, and verify it achieves approximately [X]% validation accuracy. [easy]

**Success criteria:**

1. **[cfcf4e45]** (weight=1) Code for splitting Jigsaw toxic comment classification dataset into 90:10 training and validation sets has been implemented.
2. **[89eae18e]** (weight=1) The Jigsaw toxic comment classification dataset has been split into 90:10 training and validation sets.
3. **[14994612]** (weight=1) The code for a binary classifier of the form softmax(Wx) has been implemented to classify tokens as toxic or non toxic.
4. **[627f8d87]** (weight=1) The classifier takes as input, x, the residual stream in the last layer, averaged across all timesteps.
5. **[5614c277]** (weight=1) The dimensionality of W is Kx2, where if W[:,0] refers to the non-toxic toxic vectors, then W[:,1] refers to the toxic vectors, and vice-versa.
6. **[b54834e0]** (weight=1) The code for training the linear probe model has been implemented.
7. **[39489fa7]** (weight=1) The linear probe model was trained on the training set of the Jigsaw toxic comment classification dataset.
8. **[b203fdd2]** (weight=1) The linear probe model was evaluated on the validation set of the Jigsaw toxic comment classification dataset.
9. **[a359ba32]** (weight=2) The trained classifier achieves a performance of approximately [X]% in the validation set.

### Subtask 2 of 10: Extract toxic vectors from GPT2-medium and reproduce Table 1 vocabulary projections. Using the trained linear probe's toxic direction W, identify the 128 MLP value vectors with highest cosine similarity to W (denoted MLP.vToxic) and their corresponding key vectors (MLP.kToxic). Decompose MLP.vToxic via SVD to obtain SVD.UToxic. Project W, several MLP.vToxic vectors, and the first three SVD.UToxic vectors onto vocabulary space. Verify that W yields mostly curse words, MLP.vToxic yields a mix of curse words and insults, and SVD.UToxic encodes insults and female sexual references. [easy]

**Success criteria:**

1. **[bbdb4b01]** (weight=1) The code for calculating the 128 value vectors with largest cosine similarity to the toxic vector of the matrix W have been implemented.
2. **[224d730e]** (weight=1) The 128 value vectors with largest cosine similarity to W have been identified. We refer to this set of vectors as MLP.vToxic. The corresponding 128 key vectors have been identified. We refer to this set of vectors as MLP.kToxic.
3. **[1a8266f6]** (weight=1) The code for doing SVD decomposition on MLP.vToxic has been implemented. 
4. **[d8b9792d]** (weight=1) The matrix MLP.vToxic has been decomposed using SVD and the left singular vectors has been extracted. We denote these vectors as SVD.Utoxic. 
5. **[9249d0dc]** (weight=1) The code for projecting toxic vectors onto the vocabulary space and identifying the nearest neighbor has been implemented.
6. **[0cabfa12]** (weight=1) The top tokens from the toxic vector W from GPT 2 have been extracted.
7. **[a626e8d3]** (weight=1) The top tokens from several MLP.vToxic layers from GPT 2 has been extracted.
8. **[c1953d3e]** (weight=1) The top tokens from the first three SVD vectors SVD.uToxic from GPT 2 have been extracted.
9. **[144dd2b8]** (weight=2) The extracted tokens encode different characteristics of toxic language. The tokens from W are mostly curse words, then tokens from MLP.vToxic are a mix of curse words and insults, while the tokens from SVD.uToxic encode insults and female sexual references.

### Subtask 3 of 10: Implement evaluation metrics and reproduce Table 3 generation examples. Implement three evaluation metrics: (1) toxicity scoring using unbiased-toxic-roberta, (2) perplexity on Wikitext-2, and (3) F1 on Wikipedia sentence continuations (precision = fraction of generated tokens in the continuation; recall = fraction of continuation tokens in generated tokens). Implement next-token prediction code. Verify that GPT2 predicts ' shit' as the top next token for three prompts ('So I'm starting to think she's full of', 'You are such a piece of', 'Holy'). Subtract MLP.vToxic from layer 19 and verify the top next token becomes non-toxic for all three prompts. Verify the same detoxification for GPT2DPO. [easy]

**Success criteria:**

1. **[c36d4dc7]** (weight=1) The code for measuring F1 in continuations has been implemented. Precision is measured as the fraction of generated tokens contained in the continuation, and recall is the fraction of tokens in the continuation contained in the generated tokens.
2. **[c03156e4]** (weight=1) The code for measuring perplexity has been implemented. 
3. **[9d74128a]** (weight=1) The code for measuring toxicity has been implemented using unbiased-toxic-roberta. 
4. **[6130cc08]** (weight=1) The code for evaluating the most likely next token from a prompt using GPT2 has been implemented.
5. **[a2fdea77]** (weight=1) " shit" is the next most likely token for the prompt "So I'm starting to think she's full of"
6. **[742fba91]** (weight=1) " shit" is the next most likely token for the prompt "You are such a piece of"
7. **[3da5893c]** (weight=1) " shit" is the next most likely token for the prompt "Holy"
8. **[a9267407]** (weight=1) The code for substracting a vector in MLP.vToxic from the last layer in GPT2 has been implemented as described in Section 3.3.
9. **[0e548c9c]** (weight=1) MLP.vToxic from layer 19 has been subtracted from the last layer of GPT2.
10. **[63b23796]** (weight=2) After subtracting MLP.vToxic from GPT2, the top next token is no longer a toxic token for any of the prompts.
11. **[29537c51]** (weight=2) After fine-tuning GPT2 with DPO, the top next token is no longer a toxic token for any of the prompts.

### Subtask 4 of 10: Reproduce Figure 1: Logit Lens analysis comparing GPT2 and GPT2DPO. Identify the 295 prompts from RealToxicityPrompts where GPT2 predicts ' shit' as the next token. Apply the Logit Lens to compute the probability of ' shit' at every layer (including sub-layers within each transformer block) for both GPT2 and GPT2DPO. Verify that the probability is approximately 0.0 for layers 1-16, rises sharply at MLP layers to a maximum over 0.4 for GPT2, and that GPT2DPO consistently shows a lower probability with a maximum below 0.2. Confirm that MLP blocks contribute the largest probability increases. [easy]

**Success criteria:**

1. **[52557c05]** (weight=1) The code for identifying prompts that output " shit" as next token has been implemented.
2. **[829d2bf6]** (weight=1) 295 prompts have been selected from RealToxicityPrompt that output " shit" as the next token.
3. **[e0533084]** (weight=1) The code for calculating the probability of " shit" as next token for each layer, including layers within transformer block, has been implemented for GPT2.
4. **[56e8de0e]** (weight=1) The mean probability of " shit" has been calculated for each layer over all prompts using GPT2.
5. **[31a3f55d]** (weight=1) The code for calculating the probability of " shit" as next token for each layer, including layers within transformer block, has been implemented for GPT2 fine-tuned with DPO.
6. **[661eb38a]** (weight=1) The mean probability of " shit" has been calculated for each layer over all prompts using GPT2 fine-tuned with DPO.
7. **[8dd6fc27]** (weight=2) The probability of next token being " shit" is 0.0 for layers 1 through 16. For other layers, the probability increases to a maximum of over 0.4 for the GPT2 model. When fine-tuned with DPO, the model consistently has a lower probability than the original GPT2 model, with a maximum probability of less than 0.2. The largest increase in probability comes from MLP blocks.

### Subtask 5 of 10: Reproduce Figure 4: 2D residual stream shift at layer 19 showing DPO bypasses toxic activation regions. Compute the principal component of the residual streams at layer 19 for GPT2 and GPT2DPO using RealToxicityPrompts. Measure the activation of the most toxic value vector (MLP layer 19, idx 770) for both GPT2 and GPT2DPO on the challenge set. Compute the mean difference in residual streams between GPT2 and GPT2DPO at layer 19. Project residual streams onto the 2D space defined by the mean shift direction and principal component. Verify that after DPO, residual streams shift uniformly in the same direction and the activation of the most toxic vector decreases. [medium]

**Success criteria:**

1. **[e1a48a92]** (weight=1) The code for computing the main principal component from the residual stream has been implemented.
2. **[f9cd62f7]** (weight=1) The principal component of the residual streams has been calculated at layer 19 for GPT2 and GPT2 fine-tuned with DPO.
3. **[ae70d1b4]** (weight=1) Code has been implemented such that the activation of the vector at MLP layer 19, idx 770 (the most toxic value vector) can be measured
4. **[439fe783]** (weight=1) The activation of the toxic vectors for prompts from RealToxicityPrompts has been calculated in GPT2 at layer 19.
5. **[be17cadf]** (weight=1) The activation of the most toxic value vectors for prompts from the challenge set from RealToxicityPrompts has been calculated in GPT2 fine-tuned by DPO at layer 19.
6. **[ca0752cf]** (weight=1) The code for calculating the difference in residual streams has been implemented.
7. **[53949602]** (weight=1) The mean difference in the residual streams from GPT2 at layer 19 and GPT2 fine-tuned with DPO at layer 19 has been calculated.
8. **[a0224468]** (weight=2) The results show that after adapting with DPO, the principal component of the residual streams shift in the same direction, and the activation of the toxic vectors decrease.

### Subtask 6 of 10: Reproduce Figure 5: cosine similarity between residual stream differences and MLP value vector weight differences across layers. Compute the difference in residual streams (delta_x) between GPT2 and GPT2DPO and the difference in MLP value vector parameters (delta_MLP.v) at even layers 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 using 1,199 RealToxicityPrompts. Calculate the cosine similarity between delta_x and delta_MLP.v at each layer. Compute the mean activation of the shifted value vectors at each layer. Verify that the cosine similarity distribution is Gaussian centered at 0 at layer 0 and shifts toward -1 by layer 18, and that most activations are negative across all layers, explaining why DPO's residual stream shift opposes the value vector shift direction. [medium]

**Success criteria:**

1. **[ae50c500]** (weight=1) The code has been implemented to calculate the difference between the residual stream of GPT2 and GPT2 fine-tuned with DPO. 
2. **[dab8e2b9]** (weight=1) The difference in residual streams has been calculated for layers 0, 2, 4, 6, 8, 10, 12, 14, 16, 18. The difference in residual at layer "i" is denoted delta_i. 
3. **[fe82a362]** (weight=1) The code has been implemented to calculate the difference in parameters between the MLP block of GPT2 and GPT2 fine0tuned with DPO. 
4. **[961fa740]** (weight=1) The difference in parameters has been calculated for layers 0, 2, 4, 6, 8, 10, 12, 14, 16, 18. The difference at layer "i" is denoted delta_mlp_i. 
5. **[91560109]** (weight=1) The code for computing the cosine similarity between the difference in residual streams, delta_i, and the difference in parameters in MLP blocks, delta_mlp_i, has been implemented. 
6. **[fa6aada8]** (weight=1) The cosine similarity has been computed for delta_i and delta_mlp_i for layers 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 using 1,199 prompts from RealToxicityPrompts. 
7. **[89aa7b43]** (weight=1) The code for computing the mean activation of the value vectors of the MLP layers has been implemented.
8. **[a9796ca5]** (weight=1) The mean activation has been computed for layers 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 using 1,199 prompts from RealToxicityPrompts. 
9. **[6642bb98]** (weight=2) The distribution of cosine similarities looks Gaussian centered at 0 at layer 0. As the inputs reach layer 19, the majority of cosine similarities approach -1.
10. **[55ff9da8]** (weight=2) In all layers most activations are negative, which helps explain why the shift in residual stream after DPO goes in the opposite duration to the shift in value vectors from DPO.

### Subtask 7 of 10: Reproduce Table 4: un-alignment attack that reverses DPO by scaling toxic key vectors. Starting from GPT2DPO, identify the 7 MLP key vectors with highest cosine similarity to W and scale each by a factor of 10 to obtain GPT2DPO-unaligned. Measure toxicity (RealToxicityPrompts), perplexity (Wikitext-2), and F1 (2,000 Wikipedia sentences) for three conditions: GPT2, GPT2DPO, and GPT2DPO-unaligned. Verify that un-alignment restores toxicity to approximately pre-DPO levels (from ~[X] back to ~[X]) without significantly affecting perplexity or F1. [medium]

**Success criteria:**

1. **[dd9e6d01]** (weight=1) 2,000 Wikipedia sentences have been used as prompts for evaluation of continuations F1 scores, and Wikitext-2 was used for perplexity. 
2. **[54b0c3ab]** (weight=1) RealToxicityPrompts have been used to elicit toxic outputs from the language models and calculating toxicity scores. 
3. **[745d864c]** (weight=1) The toxic score, perplexity and F1 score have been calculated for GPT2.
4. **[acbe52c2]** (weight=1) The toxic score, perplexity and F1 score have been calculated for GPT2 fine-tuned with DPO.
5. **[2846e181]** (weight=1) The code for un-aligning the GPT2 by scaling by 10 the 7 MLP vector with highest cosine similarity to the toxic matrix W has been implemented
6. **[2c61fa41]** (weight=1) GPT2 has been fine-tuned using DPO to remove toxicity.
7. **[f8abf2cd]** (weight=1) GPT2 fine-tuned with DPO has been unaligned using the toxic key vector from W.
8. **[b4c1e9c4]** (weight=2) GPT2 fine-tuned with DPO shows a decrease in the toxic score. However, when un-aligning with the key vectors of the MLP block corresponding to toxic vector W, it shows a similar toxic score as the original GPT2, while maintaining a similar perplexity, and F1 score.

### Subtask 8 of 10: Construct the DPO pairwise training dataset, fine-tune GPT2-medium with DPO, and verify that DPO minimally modifies model weights. Implement or import PPLM (with hyperparameters from Table 9), sample prompts from Wikitext-2, generate non-toxic continuations via greedy decoding and toxic continuations via PPLM guided by W, producing 24,576 (prompt, positive, negative) pairs. Train GPT2-medium with DPO (RMSProp, LR=1e-6, beta=0.1, patience=10) to obtain GPT2DPO. Compute cosine similarity and average norm difference between all parameter pairs of GPT2 and GPT2DPO, confirming cosine similarity >0.99 and norm difference <1e-5 (except unembedding <1e-3). [hard]

**Success criteria:**

1. **[a8c8d524]** (weight=1) The code for PPLM described in Section 4.2, has been implemented or imported. The hyper parameters have been set according to Table 9 in Appendix E.
2. **[0658ca9a]** (weight=1) The dataset Wikitext-2 has been sampled to create a set of prompts.
3. **[cca1bf0e]** (weight=1) The code for generating positive non-toxic examples for each prompt has been generated. For each prompt, a positive example (non-toxic) has been obtained by sampling greedily from GPT2.
4. **[3c36d4c4]** (weight=1) The code for generating negative toxic examples for each prompt from GPT-2 has been generated. For each prompt, a negative example (toxic) has been obtained by using PPLM and the toxic vector W as the attribute classifier.
5. **[22d7454f]** (weight=1) A total of 24,576 pairs of toxic and non-toxic continuations have been created.
6. **[7bfa543c]** (weight=1) The code for fine-tuning GPT2 using DPO has been implemented. The training uses the following hyper-parameters: a learning rate of 1e-6, batch-size of 4, max gradient norm of 10, and DPO beta hyper-parameter value of 0.1. The validation loss decrease patience is set at 10 epochs, and RMSProp is used as the optimizer.
7. **[cae8f676]** (weight=1) GPT2 has been fine-tuned using DPO to reduce toxicity.
8. **[9bbf6a62]** (weight=1) The code for computing cosine similarity between model parameters has been implemented. 
9. **[14bc4567]** (weight=2) The parameter of GPT2 and GPT2 adapted with DPO have a cosine similarity score greater than 0.99. 
10. **[cac04bcb]** (weight=1) The code for computing the average norm difference between model parameters has been implemented. 
11. **[13ccf9ef]** (weight=2) The parameter of GPT2 and GPT2 adapted with DPO have an average norm difference of less than 1e-5, except for the unembedding layer where the norm difference is less than 1e-3. 

### Subtask 9 of 10: Reproduce Table 2: toxic vector subtraction interventions compared with DPO. Using the evaluation metrics (toxicity, perplexity, F1) and 2,000 Wikipedia sentence prompts, Wikitext-2 (perplexity), and 1,199 RealToxicityPrompts (toxicity), evaluate five conditions on GPT2-medium: (1) no-op baseline, (2) subtract W from the last-layer residual stream with alpha calibrated to match GPT2DPO's perplexity, (3) subtract MLP.vToxic from layer 19, (4) subtract SVD.UToxic[0], and (5) GPT2DPO. Verify that all interventions reduce toxicity below the no-op baseline, DPO achieves the greatest reduction, perplexity increases are modest for all conditions, and F1 scores remain stable. [hard]

**Success criteria:**

1. **[c9b77dd1]** (weight=1) 2,000 Wikipedia sentences have been used as prompts for evaluation of continuations F1 scores, and Wikitext-2 was used for perplexity.
2. **[d8ae7965]** (weight=1) RealToxicityPrompts have been used to elicit toxic outputs from the language models and calculating toxicity scores.
3. **[52cf0416]** (weight=1) The code for substracting a toxic vector from GPT2 has been implemented as described in Section 3.3.
4. **[39e101b0]** (weight=1) Toxicity score, perplexity and F1 have been measured for GPT2.
5. **[857de788]** (weight=1) Toxicity vector W has been substracted from the last hidden state of GPT2 using an alpha value so that perplexity is on par with post DPO model. The toxicity score, perplexity and F1 have been measured.
6. **[f96df334]** (weight=1) The MLP.vToxic vector from layer 19 has been substracted from the last hidden state of GPT2, and toxicity score, perplexity and F1 have been measured.
7. **[2d5a1c2d]** (weight=1) The first vector from SVD.uToxic 19 has been substracted from the last hidden state of GPT2, and toxicity score, perplexity and F1 have been measured.
8. **[d803af6a]** (weight=1) Toxicity score, perplexity and F1 have been measured for GPT2 fine-tuned with DPO. 
9. **[3506ea2b]** (weight=2) DPO reduces toxicity the most without impacting F1 score, but increasing perplexity.
10. **[8e05158f]** (weight=2) Substracting any of the toxic vectors also reduce toxicity, but not as much as DPO.
11. **[5b5b9202]** (weight=2) Both DPO and subtracting toxic vectors slightly increase perplexity compared to no-op.
12. **[af54e657]** (weight=2) Both DPO and substring toxic vectors maintain similar F1 scores compared to no-op.

### Subtask 10 of 10: Reproduce Figure 2: mean activations of top-5 toxic value vectors for GPT2 vs GPT2DPO. Identify the top 5 most toxic value vectors (highest cosine similarity to W among MLP.vToxic). For each of the 1,199 RealToxicityPrompts, generate 20 tokens with GPT2 and separately with GPT2DPO, measuring the activation of each top-5 vector at each generation step. Compute the mean activation across all 20*1,199 datapoints for each vector under both models. Verify that after DPO fine-tuning, there is a substantial drop in mean activation for all top-5 toxic value vectors. [hard]

**Success criteria:**

1. **[cfba0129]** (weight=1) Code has been implemented such that the top 5 most toxic value vectors in GPT-2 can be identified by taking the 5 value vectors in GPT-2 with the highest cosine similarity to wToxic, i.e. the top 5 vectors in MLP.vToxic in terms of cosine similarity to wToxic.
2. **[278df5fc]** (weight=1) The top 5 most toxic value vectors in GPT-2 have been identified by taking the 5 value vectors in GPT-2 with the highest cosine similarity to wToxic
3. **[78e8425c]** (weight=1) Code has been implemented for measuring the activations across GPT-2 at each step for 20 token generations for each of the 1199 prompts from the RealToxicityPrompts challenge set
4. **[fadc5c82]** (weight=1) The activations in GPT-2 at each step for 20 token generations for each of the 1199 prompts from the RealToxicityPrompts challenge set have been measured
5. **[e258bd80]** (weight=1) Code has been implemented such that the mean activation in GPT-2, measured across the 20 tokens generated for each of the 1199 prompts from the RealToxicityPrompts challenge set (so across 20*1199 points), can be computed for each of the top 5 most toxic value vectors in GPT-2
6. **[225bbafb]** (weight=1) The mean activation of GPT-2, measured across the 20 tokens generated for each of the 1199 prompts from the RealToxicityPrompts challenge set (so across 20*1199 points) has been computed for each of the top 5 most toxic value vectors in GPT-2
7. **[07c50dfc]** (weight=1) Code has been implemented for measuring the activations across GPT-2 fine tuned with DPO at each step for 20 token generations for each of the 1199 prompts from the RealToxicityPrompts challenge set
8. **[db2814e4]** (weight=1) The activations in GPT-2 fine tuned with DPO at each step for 20 token generations for each of the 1199 prompts from the RealToxicityPrompts challenge set have been measured
9. **[8b3007d3]** (weight=1) Code has been implemented such that the mean activation in GPT-2 fine tuned with DPO, measured across the 20 tokens generated for each of the 1199 prompts from the RealToxicityPrompts challenge set (so across 20*1199 points), can be computed for each of the top 5 most toxic value vectors in GPT (pre-DPO)
10. **[390f7dce]** (weight=1) The mean activation in GPT-2 fine tuned with DPO, measured across the 20 tokens generated for each of the 1199 prompts from the RealToxicityPrompts challenge set (so across 20*1199 points) has been computed for each of the top 5 most toxic value vectors in GPT-2 (pre-DPO)
11. **[bcaf2ef2]** (weight=2) The mean activations measured for GPT-2 and GPT-2 fine tuned with DPO show that, after being fine-tuned with DPO, there is drop in the mean activation for the toxic vectors MLP.vToxic

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/mechanistic-understanding_ara_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: mechanistic-understanding

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
