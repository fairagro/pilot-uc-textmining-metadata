import os
import json
import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from code.Experiments.generate_ner_prompt import generate_ner_prompts


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
def perform_ner_with_qwen(model, tokenizer, text, max_length=1024):
    system_prompt, user_prompt = generate_ner_prompts(text)
    prompt = f"{system_prompt}\n\n{user_prompt}"

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length, padding=True).to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=1500,
        temperature=0.7,
        top_p=0.9,
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


# Step 5: Process Multiple Text Files
import os
from datasets import load_dataset


def process_text_files(input_dir, model, tokenizer, output_dir):
    """
    Process texts directly from a Hugging Face dataset.

    Parameters
    ----------
    input_dir : str
        Hugging Face dataset name, e.g.
        "IT-ZBMED/Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
    model :
        Model used by perform_ner_with_qwen().
    tokenizer :
        Tokenizer used by perform_ner_with_qwen().
    output_dir : str
        Directory where the annotated files are saved.
    """

    i = 0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the document-level version of the dataset
    dataset = load_dataset(
        input_dir,
        "doc_split"
    )

    # Process both train and test splits
    for split_name in dataset:
        for example in dataset[split_name]:

            filename = example["file_name"]

            # Reconstruct the full document from the token list
            text = " ".join(example["Tokens"])

            output_text_path = os.path.join(
                output_dir,
                filename.replace(".txt", "_annotated.txt")
            )

            print(f"Processing {filename}...")

            ner_result = perform_ner_with_qwen(
                model,
                tokenizer,
                text
            )

            with open(
                output_text_path,
                "w",
                encoding="utf-8"
            ) as file:
                file.write(ner_result)

            print(f"NER results saved to {output_text_path}")

            i += 1

            if i == 10:
                return

# Step 6: Main Execution
if __name__ == "__main__":
    input_dir = "IT-ZBMED/Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
    output_dir = "Code/Experiments/filtered_df_soil_crop_year_LTE_test_annotated_Qwen2.5-32B-Instruct"  # Change to the desired output directory path
    local_model_path = "Code/Experiments/local_models/Qwen2.5-32B-Instruct"

    qwen_model, qwen_tokenizer = load_qwen_model(local_model_path)
    process_text_files(input_dir, qwen_model, qwen_tokenizer, output_dir)

    print("NER processing complete.")