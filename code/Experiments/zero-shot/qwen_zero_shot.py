import os
import json
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

from code.Experiments.evaluation import evaluate_all, extract_prediction_json
from code.Experiments.generate_ner_prompt import generate_ner_prompts


HF_DATASET = (
    "IT-ZBMED/"
    "Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
)

DATASET_CONFIG = "doc_split"

DEFAULT_MODEL_PATH = (
    "Code/Experiments/local_models/"
    "Qwen2.5-32B-Instruct"
)


# Step 1: Load Qwen 2.5-32B Model and Tokenizer
def load_qwen_model(model_path):
    print("Loading Qwen 2.5-32B model and tokenizer from local directory...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("Qwen 2.5-32B model and tokenizer loaded from local path.")
    return model, tokenizer


# Step 3: Perform NER with Qwen 2.5-32B
def perform_ner_with_qwen(
    model,
    tokenizer,
    text,
    max_input_tokens=4096,
    max_new_tokens=1512
):
    system_prompt, user_prompt = generate_ner_prompts(text)
    prompt = f"{system_prompt}\n\n{user_prompt}"

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
        padding=True
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id
        )

    generated_tokens = outputs[0][inputs.input_ids.shape[-1]:]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return response.strip()


# Step 5: Process Multiple Text Files
def process_text_files(
    test_dataset,
    model,
    tokenizer,
    output_dir,
    max_input_tokens,
    max_new_tokens
):
    """
    Process the Hugging Face TEST split.

    Parameters
    ----------
    test_dataset :
        Hugging Face test split.
    model :
        Model used by perform_ner_with_qwen().
    tokenizer :
        Tokenizer used by perform_ner_with_qwen().
    output_dir : str
        Directory where the annotated files are saved.
    """

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    print(
        f"Processing {len(test_dataset)} "
        "test documents..."
    )

    for example in test_dataset:

        filename = example["file_name"]

        # Reconstruct the full document from the token list
        text = " ".join(example["Tokens"])

        output_text_path = os.path.join(
            output_dir,
            filename.replace(".txt", "_annotated.txt")
        )

        if os.path.exists(output_text_path):
            prediction = extract_prediction_json(
                output_text_path
            )

            if prediction is not None:
                print(
                    f"Skipping {filename} "
                    "(already processed)."
                )
                continue

            print(
                f"Existing result for {filename} "
                "is invalid. Reprocessing..."
            )

        print(f"Processing {filename}...")

        ner_result = perform_ner_with_qwen(
            model,
            tokenizer,
            text,
            max_input_tokens,
            max_new_tokens
        )

        with open(
            output_text_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(ner_result)

        print(f"NER results saved to {output_text_path}")

# Step 6: Main Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset_name",
        default=HF_DATASET,
        help="Hugging Face dataset repository."
    )

    parser.add_argument(
        "--dataset_config",
        default=DATASET_CONFIG,
        help="Hugging Face dataset configuration."
    )

    parser.add_argument(
        "--output_dir",
        default=(
            "Code/Experiments/"
            "filtered_df_soil_crop_year_LTE_test_annotated_Qwen2.5-32B-Instruct"
        ),
        help="Directory for raw Qwen outputs."
    )

    parser.add_argument(
        "--output_dir_json",
        default="Code/Experiments/results/zero_shot_qwen",
        help="Directory for evaluation metrics."
    )

    parser.add_argument(
        "--model_name",
        default="Qwen2.5-32B-Instruct",
        help="Human-readable model name used in evaluation results."
    )

    parser.add_argument(
        "--model_path",
        default=DEFAULT_MODEL_PATH,
        help="Local Qwen model path."
    )

    parser.add_argument(
        "--max_input_tokens",
        type=int,
        default=4096,
        help="Maximum input prompt tokens."
    )

    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=1512,
        help="Maximum number of generated output tokens."
    )

    args = parser.parse_args()

    dataset = load_dataset(
        args.dataset_name,
        args.dataset_config
    )

    test_dataset = dataset["test"]

    qwen_model, qwen_tokenizer = load_qwen_model(
        args.model_path
    )

    process_text_files(
        test_dataset,
        qwen_model,
        qwen_tokenizer,
        args.output_dir,
        args.max_input_tokens,
        args.max_new_tokens
    )

    log_dir = os.environ.get(
        "LOG_DIR"
    )

    evaluate_all(
        args.model_name,
        test_dataset,
        args.output_dir,
        args.output_dir_json,
        None,
        log_dir
    )

    print("NER processing complete.")
