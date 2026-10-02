# Experiments

This directory contains the Named Entity Recognition (NER) experiments for the pilot use case.

The experiments use the Hugging Face dataset:

```text
IT-ZBMED/Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment
```

## Directory Structure

- [zero-shot](zero-shot): foundation-model NER without retrieved examples.
- [fiveshot](fiveshot): foundation-model NER with retrieval-augmented five-shot examples.
- [finetuning](finetuning): encoder token-classification fine-tuning.
- [generate_ner_prompt.py](generate_ner_prompt.py): shared prompt builder for foundation-model approaches.
- [evaluation.py](evaluation.py): shared span-based evaluator for foundation-model outputs.

## Evaluation

The foundation-model approaches, both zero-shot and five-shot, use the document-level dataset configuration:

```text
doc_split
```

They run on the full test split and use [evaluation.py](evaluation.py), which evaluates JSON entity predictions with:

- exact entity span matching
- partial entity span overlap matching
- per-class metrics
- overall micro metrics
- macro F1

The fine-tuning approach is different by design. It uses the sentence-level dataset configuration:

```text
sentence_split
```

It is evaluated as a Hugging Face token-classification NER task using `seqeval` through `Trainer`.

## Zero-Shot Experiments

These scripts run NER without training examples in the prompt.

### ChatGPT / GPT

Requires `OPENROUTER_API_KEY`.

```bash
export OPENROUTER_API_KEY='your_api_key'

python code/Experiments/zero-shot/chatgpt.py \
  --output_dir code/Experiments/results/zero_shot_gpt5/raw \
  --output_dir_json code/Experiments/results/zero_shot_gpt5/metrics \
  --model_name "GPT-5"
```

### DeepSeek

Requires `OPENROUTER_API_KEY`.

```bash
export OPENROUTER_API_KEY='your_api_key'

python code/Experiments/zero-shot/deepseek.py \
  --output_dir code/Experiments/results/zero_shot_deepseek/raw \
  --output_dir_json code/Experiments/results/zero_shot_deepseek/metrics \
  --model_name "DeepSeekV3"
```

### Qwen

Requires a local Qwen model.

```bash
python code/Experiments/zero-shot/qwen_zero_shot.py \
  --model_path Code/Experiments/local_models/Qwen2.5-32B-Instruct \
  --output_dir code/Experiments/results/zero_shot_qwen/raw \
  --output_dir_json code/Experiments/results/zero_shot_qwen/metrics \
  --model_name "Qwen2.5-32B-Instruct"
```

## Five-Shot Experiments

These scripts retrieve similar examples from the training split with FAISS and add them to the prompt.

### ChatGPT / GPT

Requires `OPENROUTER_API_KEY`.

```bash
export OPENROUTER_API_KEY='your_api_key'

python code/Experiments/fiveshot/chatgpt.py \
  --output_dir code/Experiments/results/fiveshot_gpt/raw \
  --output_dir_json code/Experiments/results/fiveshot_gpt/metrics \
  --model_name "GPT-5" \
  --model "openai/gpt-5" \
  --top_k 5
```

### DeepSeek

Requires `OPENROUTER_API_KEY`.

```bash
export OPENROUTER_API_KEY='your_api_key'

python code/Experiments/fiveshot/deepseek.py \
  --output_dir code/Experiments/results/fiveshot_deepseek/raw \
  --output_dir_json code/Experiments/results/fiveshot_deepseek/metrics \
  --model_name "DeepSeekV3" \
  --top_k 5
```

### Qwen

Requires a local Qwen model.

```bash
python code/Experiments/fiveshot/qwen.py \
  --model_path Code/Experiments/local_models/Qwen2.5-32B-Instruct \
  --output_dir code/Experiments/results/fiveshot_qwen/raw \
  --output_dir_json code/Experiments/results/fiveshot_qwen/metrics \
  --model_name "Qwen2.5-32B-Instruct" \
  --top_k 5
```

## Fine-Tuning

The fine-tuning script trains an encoder model for token classification and evaluates it with Hugging Face `Trainer` metrics.

```bash
export WANDB_API_KEY='your_wandb_key'

python code/Experiments/finetuning/encoder_finetuning.py
```

The model checkpoint is configured in [finetuning/encoder_finetuning.py](finetuning/encoder_finetuning.py).

## Model-Free Evaluation Test

A dummy dataset test checks the shared foundation-model evaluator without calling any model or external API.

```bash
python3 -m unittest tests/test_experiments_evaluation_dummy.py
```

The test uses known exact and partial F1 scores to verify the evaluator logic.
