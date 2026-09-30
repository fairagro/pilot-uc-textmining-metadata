# Codebase Directory

This directory includes all the software developped for the pilot use case. As the use case is divided into different phases, each 
component is ran separately in its phase and each component is described as follows:

---

## Directory Structure
Each directory is for a specific task/RDI \
We have the following:\
* [utils](utils): Includes utility functions.
* [OpenAgrar](OpenAgrar): Includes code to download, manipulate and save metadata from OpenAgrar RDI.
* [Bonares](Bonares): Includes code to download, manipulate and save metadata from OpenAgrar RDI.
* [Pre-annotations](Pre-annoatations): This includes the pre-annotations and processing pipeline for the data downloaded from the resources.
* [corpus_creation](corpus_creation): This includes the pipelines to generate the final csv and JSON files of the annotated corpus in train and test splits.
* [Experiments](Experiments): This directory contains the scripts to run the Named Entity Recognition (NER) experiments using different models and approaches.

## Experiments

The `Experiments` directory includes various approaches for NER:

### 1. Zero-shot Experiments
Located in `code/Experiments/zero-shot`. These scripts run NER without any training examples.
- **ChatGPT / DeepSeek**: Use OpenRouter API.
  ```bash
  export OPENROUTER_API_KEY='your_api_key'
  python code/Experiments/zero-shot/chatgpt.py
  python code/Experiments/zero-shot/deepseek.py
  ```
- **Qwen**: Runs a local model.
  ```bash
  python code/Experiments/zero-shot/qwen_zero_shot.py
  ```

### 2. Five-shot (RAG) Experiments
Located in `code/Experiments/fiveshot`. These scripts use Retrieval-Augmented Generation to find similar examples from the training set and use them as context.
- **ChatGPT / DeepSeek**:
  ```bash
  export OPENROUTER_API_KEY='your_api_key'
  python code/Experiments/fiveshot/chatgpt.py --output_dir results/chatgpt --output_dir_json results/chatgpt_json --model_name "GPT-4o"
  ```

### 3. Fine-tuning
Located in `code/Experiments/finetuning`.
- **Encoder Fine-tuning**: Fine-tunes an encoder model (e.g., XLM-RoBERTa) using Optuna for hyperparameter optimization and Weights & Biases for logging.
  ```bash
  export WANDB_API_KEY='your_wandb_key'
  python code/Experiments/finetuning/encoder_finetuning.py
  ```

## Use Instructions 
Based on the task or the pipeline you would like to use, please refer to the directory containing this component.