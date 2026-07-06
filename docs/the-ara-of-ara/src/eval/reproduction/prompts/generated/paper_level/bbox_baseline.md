# Full Paper Reproduction: bbox

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all 10 subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bbox_baseline_seed0/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bbox_baseline_seed0/RESULT.md` — append results after each subtask

## Source Material

You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/pdfs/bbox.pdf` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/repos/bbox` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bbox_baseline_seed0/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

### Subtask 1 of 10: Implement the EBM adapter architecture for BBOX-ADAPTER. Set up both DeBERTa-v3-base (0.1B) and DeBERTa-v3-large (0.3B) backbones with scalar classification heads, and implement the NCE loss from Equation 3 with spectral normalization. Configure the adapter to accept (x,y) text pairs and output scalar energy scores. Do NOT train or evaluate — implementation only. [easy]

**Success criteria:**

1. **[deberta-]** (weight=1) The deberta-v3-base model has been implemented for StrategyQA with the hyperparameters specified in Appendix H.2.
2. **[deberta-]** (weight=1) The deberta-v3-base model has been implemented for GSM8K with the hyperparameters specified in Appendix H.2.
3. **[deberta-]** (weight=1) The deberta-v3-large model has been implemented for StrategyQA with the hyperparameters specified in Appendix H.2.
4. **[deberta-]** (weight=1) The deberta-v3-large model has been implemented for GSM8K with the hyperparameters specified in Appendix H.2.
5. **[adapter-]** (weight=1) The adapter accepts input text pairs (x,y) and processes them through the DeBERTa encoder.
6. **[adapter-]** (weight=1) The adapter outputs a scalar score $g_{\theta}(x,y)$ representing the energy value for the input pair.
7. **[positive]** (weight=1) The positive sample terms $-\mathbb{E}_{y^+ \sim p_{data}(y|x)}[g_\theta(x,y^+)] + \alpha\mathbb{E}[g_\theta(x,y^+)^2]$ have been implemented.
8. **[negative]** (weight=1) The negative sample terms $\mathbb{E}_{y^- \sim p_\theta(y|x)}[g_\theta(x,y^-)] + \alpha\mathbb{E}[g_\theta(x,y^-)^2]$ have been implemented.
9. **[loss-com]** (weight=1) The NCE loss has been implemented according to Equation (3) in the paper, which includes: $\nabla_{\theta}\ell(\theta) = \nabla_{\theta}\{-\mathbb{E}_{y+\sim p_{data}(y|x)}[g_{\theta}(x,y+)] + \alpha\mathbb{E}[g_{\theta}(x,y+)^2] + \mathbb{E}_{y-\sim p_{\theta}(y|x)}[g_{\theta}(x,y-)] + \alpha\mathbb{E}[g_{\theta}(x,y-)^2]\}$, incorporating both positive and negative sample terms with regularization.
10. **[gradient]** (weight=1) The gradient updates $\nabla_{\theta} \mathcal{L}_{NCE}$ have been implemented with $\eta=5e-6$ as specified in Appendix H.2.
11. **[spectral]** (weight=1) Spectral normalization has been applied to the energy model $g_{\theta}$ to increase gradient stability.
12. **[model-lo]** (weight=1) Code has been written to load and initialize the deberta-v3-base model (86M) with correct model weights.
13. **[classifi]** (weight=1) The final layer has been modified to a classification head with an output dimension of 1 to ensure the adapter outputs a scalar score value.
14. **[model-lo]** (weight=1) Code has been written to load and initialize the deberta-v3-large model (304M) with correct model weights.
15. **[classifi]** (weight=1) The final layer has been modified to a classification head with an output dimension of 1 to ensure the adapter outputs a scalar score value.

### Subtask 2 of 10: Implement the sentence-level beam search inference mechanism for BBOX-ADAPTER. Implement both the single-step variant (LLM generates complete answers, adapter selects the best) and the full-step variant (iterative beam search with sentence-level factorization). Set up the LLM as a black-box proposal generator: handle prompt formatting, completion parsing, and configure generation parameters (temperature=1.0, max_length=512). Verify the beam search correctly scores candidates, prunes beams, and selects final outputs. [easy]

**Success criteria:**

1. **[sequence]** (weight=1) The decomposition of complete solution $y$ into sentence-level sequences $[s_1, s_2, ..., s_L]$ has been implemented.
2. **[autoregr]** (weight=1) The autoregressive scoring of sequences using both LLM probabilities and adapter scores has been implemented.
3. **[candidat]** (weight=1) The generation of $M$ samples per beam at each step $l$ based on $p_{LLM}(s_l|x,s_{1:l-1})$ has been implemented.
4. **[beam-sco]** (weight=1) The scoring of $nk$ candidate chains using the adapter $g_\theta(s_{1:l},x)$ has been implemented.
5. **[beam-pru]** (weight=1) The selection of top-k beams based on adapter scores has been implemented.
6. **[terminat]** (weight=1) The checking for either reaching $L$ iterations or encountering stop signals has been implemented.
7. **[final-se]** (weight=1) The selection of the highest-scoring complete solution from the $k$ final candidates has been implemented.
8. **[single-s]** (weight=1) The base model generates a set of complete answers in a single step.
9. **[single-s]** (weight=1) The adapter selects the best answer from the candidates as the final response.
10. **[full-ste]** (weight=1) The base model generates multiple solution paths using beam search.
11. **[full-ste]** (weight=1) The adapter scores and selects the top-$k$ paths at each step, maintaining a beam size of $k=3$ by default as specified in the paper.
12. **[prompt-h]** (weight=1) Code has been written to properly format and send prompts to the LLM API.
13. **[completi]** (weight=1) Code has been written to parse completion responses from the LLM API.
14. **[proposal]** (weight=1) Code has been written such that the LLM can generate candidate proposals for the adapter to score.
15. **[black-bo]** (weight=1) Code has been written such that the LLM is treated as a black box without accessing internal parameters or probabilities.

### Subtask 3 of 10: Download and prepare all four evaluation datasets (StrategyQA, GSM8K, TruthfulQA, ScienceQA) with the exact train/test splits specified in Appendix F.1. Set up the BERT-base-cased adapter backbone for TruthfulQA. Configure GPT-5-mini API access and Mixtral-8x7B model loading. Implement the few-shot CoT prompts (2-shot for StrategyQA, 4-shot for GSM8K, 1-shot for ScienceQA) as specified in Appendix J. [easy]

**Success criteria:**

1. **[gsm8k-do]** (weight=1) Code has been written to download the GSM8K questions and step-by-step solutions.
2. **[gsm8k-do]** (weight=1) The GSM8K questions and step-by-step solutions have been downloaded.
3. **[gsm8k-sp]** (weight=1) Code has been written to split the GSM8K dataset into 7473 training and 1319 test samples.
4. **[gsm8k-sp]** (weight=1) The GSM8K dataset has been split into 7473 training and 1319 test samples.
5. **[strategy]** (weight=1) Code has been written to download the StrategyQA questions and reasoning steps.
6. **[strategy]** (weight=1) The StrategyQA questions and reasoning steps have been downloaded.
7. **[strategy]** (weight=1) Code has been written to split the StrategyQA dataset into 2059 training and 229 test samples.
8. **[strategy]** (weight=1) The StrategyQA dataset has been split into 2059 training and 229 test samples.
9. **[truthful]** (weight=1) Code has been written to download the TruthfulQA questions.
10. **[truthful]** (weight=1) The TruthfulQA questions have been downloaded.
11. **[truthful]** (weight=1) Code has been written to randomly sample 100 questions for the test set and use the remaining 717 samples for training.
12. **[truthful]** (weight=1) The TruthfulQA dataset has been split into 717 training and 100 test samples.
13. **[bert-bas]** (weight=1) The bert-base-cased (110M) model has been implemented for TruthfulQA with the hyperparameters specified in Appendix H.2.
14. **[model-lo]** (weight=1) Code has been written to load the weights of the bert-base-cased (110M) model.
15. **[classifi]** (weight=1) The final layer has been modified to a classification head with an output dimension of 1 to ensure the adapter outputs a scalar score value.

### Subtask 4 of 10: Implement and execute Algorithm 1 (Online Adaptation) for BBOX-ADAPTER. Implement initialization (random adapter parameters, initial K-response sampling, ground-truth and AI-feedback positive/negative selection), the main adaptation loop (Equations 3-7: adapted sampling, positive/negative sample updates, NCE loss gradient, parameter update), and the training configuration (AdamW optimizer with lr=5e-6 and weight decay 0.01, batch size 64, 6000 steps). Train one 0.1B adapter on StrategyQA using ground-truth feedback. [medium]

**Success criteria:**

1. **[random-i]** (weight=1) Random initialization of adapter parameters $\theta_0$ has been implemented.
2. **[initial-]** (weight=1) Initial sampling of $K$ responses for each input query has been implemented: ${y_{i,j}}^K_{j=1} \sim p_{LLM}(y|x_i)$.
3. **[ground-t]** (weight=1) When ground truth data is available, positive samples are taken from ground truth solutions while negative samples are generated using an adapter with random parameters.
4. **[ai-feedb]** (weight=1) When ground truth data is unavailable, positive samples are selected based on AI feedback (using GPT-4) from generated candidates, while remaining candidates serve as negative samples.
5. **[eq4-impl]** (weight=1) Sampling $M$ candidates from adapted inference has been implemented as described in Equation 4 i.e., ${\hat{y}_{i,m}}^M_{m=1} \sim p_{\theta_t}(y|x_i)$
6. **[eq5-impl]** (weight=1) The update of positive samples has been implemented as described in Equation 5 i.e., $y^{(t)}_{i+} = \text{SEL}(y^{(t-1)}_{i+}, {\hat{y}_{i,m}}^M_{m=1})$
7. **[eq6-impl]** (weight=1) The update of negative samples has been implemented as described in Equation 6 i.e., $y^{(t)}_{i-} = {\hat{y}_{i,m} | \hat{y}_{i,m} \neq y^{(t)}_{i+}}^M_{m=1}$
8. **[eq3-impl]** (weight=1) The computation of the loss gradient has been implemented as described in Equation 3 i.e., $\nabla_\theta \ell(\theta_t)$ using $y^{(t)}_{i+}$ and $y^{(t)}_{i-}$
9. **[eq7-impl]** (weight=1) The parameter update has been implemented as described in Equation 7 i.e., $\theta_{t+1} = \theta_t - \eta \nabla_\theta \ell(\theta_t)$
10. **[optimize]** (weight=1) The AdamW optimizer has been configured with learning rate 5e-6 and weight decay 0.01.
11. **[batch-co]** (weight=1) The training loop has been implemented to process data in batches of size 64 and run for 6000 training steps as specified in Appendix H.2.
12. **[adapter-]** (weight=1) The adapter has been trained using the NCE loss and spectral normalization for the specified number of steps.
13. **[strategy]** (weight=1) The training process for a dedicated 0.1B adapter on the StrategyQA dataset has been executed.

### Subtask 5 of 10: Evaluate BBOX-ADAPTER with Ground-Truth feedback against the CoT baseline on GPT-5-mini for StrategyQA and GSM8K (partial Table 2). Run the CoT baseline on both datasets. Train task-specific 0.1B and 0.3B adapters for each dataset, select the best performer, and evaluate with ground-truth feedback. Verify that BBOX-ADAPTER (GT) improves over CoT by approximately [X]% on StrategyQA and [X]% on GSM8K. [medium]

**Success criteria:**

1. **[azure-ap]** (weight=1) API access has been set up for text generation using GPT-5-mini, supporting the following features: (1) prompt-based text generation, (2) adjustable sampling temperature, and (3) control over maximum output length.
2. **[gpt-gene]** (weight=1) The model is configured with temperature 1.0 and a maximum length of 512 tokens for generation.
3. **[cot-exec]** (weight=1) The Chain-of-Thought baseline has been evaluated on the test splits of all datasets using GPT-5-mini.
4. **[cot-stra]** (weight=1) The accuracy of the base GPT-5-mini model on the StrategyQA dataset has been calculated.
5. **[cot-gsm8]** (weight=1) The accuracy of the base GPT-5-mini model on the GSM8K dataset has been calculated.
6. **[gt-adapt]** (weight=1) The adapter has been trained using ground truth data.
7. **[gt-evalu]** (weight=1) The ground truth adapter has been evaluated on the test splits of all datasets.
8. **[gt-acc-s]** (weight=1) The accuracy has been computed for StrategyQA.
9. **[gsm8k-sm]** (weight=1) The training process for a dedicated 0.1B adapter on the GSM8K dataset has been executed.
10. **[gsm8k-la]** (weight=1) The training process for a dedicated 0.3B adapter on the GSM8K dataset has been executed.
11. **[performa]** (weight=1) Code has been written to compare adapter sizes and select the best performer.
12. **[performa]** (weight=1) The performance comparison has been run and best performers selected.
13. **[baseline]** (weight=1) The baseline model achieves an accuracy of [X]% on StrategyQA.
14. **[baseline]** (weight=1) The baseline model achieves an accuracy of [X]% on GSM8K.
15. **[gt-strat]** (weight=1) The Ground-Truth adapter achieves an improvement of [X]% on StrategyQA.

### Subtask 6 of 10: Reproduce the NCE-vs-MLM loss ablation study (Table 5). Implement the MLM baseline (masked word supervision for training, masked word probability scoring for inference). Train both NCE and MLM adapters at both sizes (0.1B and 0.3B) on StrategyQA and GSM8K. Verify that NCE consistently outperforms MLM by approximately 10 percentage points on StrategyQA regardless of adapter size (MLM: [X]%/60.41% vs NCE: [X]%/71.18%). [medium]

**Success criteria:**

1. **[mlm-trai]** (weight=1) The training pipeline using masked word supervision has been implemented.
2. **[mlm-infe]** (weight=1) The inference process using masked word probability scoring has been implemented.
3. **[deberta-]** (weight=1) The deberta-v3-base model has been implemented for ScienceQA with the hyperparameters specified in Appendix H.2.
4. **[deberta-]** (weight=1) The deberta-v3-large model has been implemented for ScienceQA with the hyperparameters specified in Appendix H.2.
5. **[size-per]** (weight=1) The accuracy metrics for both 0.1B and 0.3B adapters have been calculated.
6. **[mlm-size]** (weight=1) The results show that the MLM-based adapter achieves [X]% (0.1B) and 60.41% (0.3B) accuracy on StrategyQA.
7. **[nce-size]** (weight=1) The results show that the NCE-based adapter achieves [X]% (0.1B) and 71.18% (0.3B) accuracy on StrategyQA, showing consistent improvement of [X]% over MLM regardless of adapter size.
8. **[temperat]** (weight=1) The temperature is set to 1.0 for generation as specified in Appendix H.2.
9. **[max-leng]** (weight=1) The maximum generation length is set to 512 as specified in Appendix H.2.

### Subtask 7 of 10: Evaluate BBOX-ADAPTER with AI Feedback and Combined feedback on GPT-5-mini for StrategyQA and GSM8K (partial Table 2). Train adapters using AI feedback (GPT-4 as judge, no ground-truth labels) and combined feedback (both GT + AI). Evaluate all three feedback modes and compare. Verify that AI Feedback achieves competitive performance with GT ([X]% on StrategyQA, [X]% on GSM8K) and that Combined achieves the best results ([X]% on StrategyQA, [X]% on GSM8K). [hard]

**Success criteria:**

1. **[ai-adapt]** (weight=1) The adapter has been trained using AI feedback.
2. **[ai-evalu]** (weight=1) The AI feedback adapter has been evaluated on the test splits of all datasets.
3. **[combined]** (weight=1) The adapter has been trained using combined feedback.
4. **[combined]** (weight=1) The combined feedback adapter has been evaluated on the test splits of all datasets.
5. **[ai-feedb]** (weight=1) The AI feedback adapter achieves an improvement of [X]% on StrategyQA.
6. **[ai-feedb]** (weight=1) The AI feedback adapter achieves an improvement of [X]% on GSM8K.
7. **[combined]** (weight=1) The Combined adapter achieves an improvement of [X]% on StrategyQA.
8. **[combined]** (weight=1) The Combined adapter achieves an improvement of [X]% on GSM8K.
9. **[combined]** (weight=1) The True+Info metric has been computed for StrategyQA.
10. **[combined]** (weight=1) The True+Info metric has been computed for GSM8K.
11. **[gt-gsm8k]** (weight=1) The Ground-Truth adapter achieves an improvement of [X]% on GSM8K.

### Subtask 8 of 10: Reproduce the plug-and-play transfer evaluation on davinci-002 (partial Table 3). Set up davinci-002 API access with the specified generation parameters. Take the adapter trained on GPT-5-mini and apply it without retraining to davinci-002. Evaluate base and adapted davinci-002 on StrategyQA and TruthfulQA. Verify that adapted davinci-002 improves by [X]% on StrategyQA and [X]% on TruthfulQA. [hard]

**Success criteria:**

1. **[davinci-]** (weight=1) API access has been configured to enable text generation using davinci-002
2. **[davinci-]** (weight=1) The model is configured with temperature 1.0 and a maximum length of 512 tokens for generation as specified in Appendix H.2
3. **[base-dav]** (weight=1) The accuracy of base davinci-002 on StrategyQA has been calculated.
4. **[base-dav]** (weight=1) The accuracy of base davinci-002 on GSM8K has been calculated.
5. **[base-dav]** (weight=1) The True+Info metric of base davinci-002 on TruthfulQA has been calculated.
6. **[adapted-]** (weight=1) The accuracy of adapted davinci-002 on StrategyQA has been calculated.
7. **[adapted-]** (weight=1) The accuracy of adapted davinci-002 on GSM8K has been calculated.
8. **[adapted-]** (weight=1) The True+Info metric of adapted davinci-002 on TruthfulQA has been calculated.
9. **[davinci-]** (weight=1) The adapted davinci-002 achieves an improvement of [X]% on StrategyQA.
10. **[davinci-]** (weight=1) The adapted davinci-002 achieves an improvement of [X]% on GSM8K.
11. **[davinci-]** (weight=1) The adapted davinci-002 achieves an improvement of [X]% on TruthfulQA.
12. **[davinci-]** (weight=1) The adapted davinci-002 achieves an average improvement of [X]% across all datasets.

### Subtask 9 of 10: Reproduce the scaling analysis for beam size and online adaptation iterations (Figure 3). Configure BBOX-ADAPTER with beam sizes k=1, 3, 5 on StrategyQA and verify that increasing beam size yields [X]% average improvement. Configure online adaptation with T=0, 1, 2, 3, 4 iterations on StrategyQA and verify that (a) the un-finetuned adapter (T=0) performs worse than the base model, (b) performance surpasses the base model after T=1, and (c) improvements are consistent up to T=3. [hard]

**Success criteria:**

1. **[beam-con]** (weight=1) The adapter has been configured to run with beam sizes $k$ = 1, 3, and 5.
2. **[beam-inf]** (weight=1) The inference has been executed for each beam size configuration.
3. **[performa]** (weight=1) The performance changes across beam sizes ($k$ = 1, 3, 5) have been tracked and calculated.
4. **[beam-siz]** (weight=1) The results show that increasing the number of beams contributes to an average performance enhancement of [X]% across different adapter sizes (0.1B and 0.3B).
5. **[iteratio]** (weight=1) The online adaptation has been configured to run with $T$ = 0, 1, 2, 3, and 4 iterations.
6. **[iteratio]** (weight=1) The training and inference has been executed for each iteration configuration.
7. **[performa]** (weight=1) Code has been written to compute and save the performance changes across iteration counts.
8. **[performa]** (weight=1) The performance changes across iteration counts have been computed and saved.
9. **[initial-]** (weight=1) The results show that the un-finetuned adapter ($T=0$) performs worse than the base model.
10. **[adaptati]** (weight=1) The results show that the adapted LLM surpasses the performance of the base model after one round of adaptation.
11. **[subseque]** (weight=1) The results show that consistent improvements are observed with iterations up to $T=3$.

### Subtask 10 of 10: Reproduce the cost efficiency analysis (Table 4) comparing BBOX-ADAPTER vs Azure-SFT on StrategyQA and GSM8K. Set up and execute Azure-SFT baseline fine-tuning (epochs=3). Track and compute training costs ($), inference costs ($/1k questions), and evaluation costs ($) for both Azure-SFT and BBOX-ADAPTER (full-step variant). Verify that BBOX-ADAPTER reduces training costs by ~[X]x and inference costs by ~[X]x compared to Azure-SFT, while maintaining competitive performance. [hard]

**Success criteria:**

1. **[data-for]** (weight=1) The training data has been formatted according to Azure fine-tuning API requirements.
2. **[hyperpar]** (weight=1) The fine-tuning hyperparameters (epochs=3, batch size and learning rate as Azure OpenAI service default values) have been configured.
3. **[azure-sf]** (weight=1) Code has been written to execute fine-tuning jobs through the Azure OpenAI API.
4. **[azure-sf]** (weight=1) The fine-tuning jobs have been executed successfully for all tasks.
5. **[gpt-fine]** (weight=1) The fine-tuning hyperparameters have been configured with number of epochs set to 5.
6. **[azure-sf]** (weight=1) Code has been written to compute and save the training cost ($) for StrategyQA.
7. **[azure-sf]** (weight=1) Code has been written to compute and save the training cost ($) for GSM8K.
8. **[adapter-]** (weight=1) Code has been written to compute and save the training cost ($) for StrategyQA.
9. **[adapter-]** (weight=1) Code has been written to compute and save the training cost ($) for GSM8K.
10. **[azure-sf]** (weight=1) Code has been written to compute and save the inference cost ($/1k questions) for StrategyQA.
11. **[azure-sf]** (weight=1) Code has been written to compute and save the inference cost ($/1k questions) for GSM8K.
12. **[adapter-]** (weight=1) Code has been written to compute and save the inference cost ($/1k questions) for StrategyQA.
13. **[adapter-]** (weight=1) Code has been written to compute and save the inference cost ($/1k questions) for GSM8K.
14. **[training]** (weight=1) The results show that BBOX-ADAPTER reduces training costs by ~[X]x compared to Azure-SFT.
15. **[inferenc]** (weight=1) The results show that BBOX-ADAPTER reduces inference costs by ~[X]x compared to Azure-SFT.

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `/Users/amberljc/Desktop/github-project/writing/ara-draft/code/eval/reproduction/results/bbox_baseline_seed0/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: bbox

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
