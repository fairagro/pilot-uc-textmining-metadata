import argparse
import json
import os
import sys
from typing import Any, List

import faiss
import numpy as np
import torch
from datasets import load_dataset
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.append(os.path.abspath(".."))

from code.Experiments.evaluation import evaluate_all, extract_prediction_json
from code.Experiments.generate_ner_prompt import generate_ner_prompts

load_dotenv()


# ============================================================
# Configuration
# ============================================================

HF_DATASET = (
    "IT-ZBMED/"
    "Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
)

DATASET_CONFIG = "doc_split"

DEFAULT_MODEL_PATH = (
    "Code/Experiments/local_models/"
    "Qwen2.5-32B-Instruct"
)


LABEL_LIST = [
    "O",
    "B-soilReferenceGroup",
    "I-soilReferenceGroup",
    "B-soilOrganicCarbon",
    "I-soilOrganicCarbon",
    "B-soilTexture",
    "I-soilTexture",
    "B-startTime",
    "I-startTime",
    "B-endTime",
    "I-endTime",
    "B-city",
    "I-city",
    "B-duration",
    "I-duration",
    "B-cropSpecies",
    "I-cropSpecies",
    "B-soilAvailableNitrogen",
    "I-soilAvailableNitrogen",
    "B-soilDepth",
    "I-soilDepth",
    "B-region",
    "I-region",
    "B-country",
    "I-country",
    "B-longitude",
    "I-longitude",
    "B-latitude",
    "I-latitude",
    "B-cropVariety",
    "I-cropVariety",
    "B-soilPH",
    "I-soilPH",
    "B-soilBulkDensity",
    "I-soilBulkDensity",
]


ENTITY_TO_CATEGORY = {
    "cropSpecies": "Crops",
    "cropVariety": "Crops",

    "soilTexture": "Soil",
    "soilReferenceGroup": "Soil",
    "soilDepth": "Soil",
    "soilBulkDensity": "Soil",
    "soilPH": "Soil",
    "soilOrganicCarbon": "Soil",
    "soilAvailableNitrogen": "Soil",

    "country": "Location",
    "region": "Location",
    "city": "Location",
    "latitude": "Location",
    "longitude": "Location",

    "startTime": "Time Statement",
    "endTime": "Time Statement",
    "duration": "Time Statement",
}


# ============================================================
# Reconstruct text and character positions
# ============================================================

def tokens_to_text_and_offsets(tokens):
    text_parts = []
    offsets = []
    position = 0

    for i, token in enumerate(tokens):
        if i > 0:
            text_parts.append(" ")
            position += 1

        start = position
        text_parts.append(token)
        position += len(token)
        end = position

        offsets.append((start, end))

    return "".join(text_parts), offsets


# ============================================================
# Convert BIO annotations into prompt JSON
# ============================================================

def bio_to_json(tokens, ner_tags, label_list):
    text, offsets = tokens_to_text_and_offsets(tokens)

    result = {
        "Crops": [],
        "Soil": [],
        "Location": [],
        "Time Statement": [],
    }

    current_entity = None
    current_start = None
    current_end = None

    def save_current_entity():
        nonlocal current_entity
        nonlocal current_start
        nonlocal current_end

        if current_entity is None:
            return

        category = ENTITY_TO_CATEGORY.get(current_entity)

        if category is not None:
            result[category].append({
                current_entity: {
                    "value": text[current_start:current_end],
                    "span": [
                        current_start,
                        current_end,
                    ],
                }
            })

        current_entity = None
        current_start = None
        current_end = None

    for i, tag_id in enumerate(ner_tags):
        label = label_list[tag_id]

        if label == "O":
            save_current_entity()
            continue

        prefix, entity_type = label.split("-", 1)
        start, end = offsets[i]

        if prefix == "B":
            save_current_entity()
            current_entity = entity_type
            current_start = start
            current_end = end

        elif prefix == "I":
            if current_entity == entity_type:
                current_end = end
            else:
                save_current_entity()
                current_entity = entity_type
                current_start = start
                current_end = end

    save_current_entity()

    return text, result


# ============================================================
# Get label names from Hugging Face dataset
# ============================================================

def get_label_list(dataset):
    try:
        feature = dataset["train"].features["ner_tags"]

        if hasattr(feature, "feature"):
            class_label = feature.feature

            if hasattr(class_label, "names"):
                names = class_label.names

                print(
                    f"Loaded {len(names)} label names "
                    "directly from dataset."
                )

                return names

    except Exception as error:
        print(
            "Could not retrieve label names from dataset "
            f"features: {error}"
        )

    print("Using predefined fallback LABEL_LIST.")

    return LABEL_LIST


# ============================================================
# Prepare retrieval corpus from TRAIN split
# ============================================================

def prepare_retrieval_corpus(
    train_dataset,
    label_list,
):
    corpus_texts = []
    corpus_entities = []

    print(
        f"Preparing retrieval corpus from "
        f"{len(train_dataset)} training documents..."
    )

    for example in train_dataset:
        text, entities = bio_to_json(
            example["Tokens"],
            example["ner_tags"],
            label_list,
        )

        corpus_texts.append(text)
        corpus_entities.append(entities)

    print(
        f"Retrieval corpus contains "
        f"{len(corpus_texts)} documents."
    )

    return corpus_texts, corpus_entities


# ============================================================
# Embeddings and FAISS
# ============================================================

def embed_texts(
    embedder,
    texts: List[str],
    batch_size: int = 64,
):
    embeddings = embedder.encode(
        texts,
        convert_to_numpy=True,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings.astype("float32")


def build_index(
    embeddings: np.ndarray,
    index_path: str,
):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    if index_path:
        faiss.write_index(
            index,
            index_path,
        )

        print(
            f"FAISS index saved to: "
            f"{index_path}"
        )

    return index


def get_similar_examples(
    query_text: str,
    embedder,
    index,
    corpus_texts: List[str],
    corpus_entities: List[Any],
    top_k: int = 5,
):
    query_embedding = embedder.encode(
        [query_text],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    actual_k = min(
        top_k,
        len(corpus_texts),
    )

    similarities, indices = index.search(
        query_embedding,
        actual_k,
    )

    indices = indices[0].tolist()
    similarities = similarities[0].tolist()

    examples = [
        (
            corpus_texts[i],
            corpus_entities[i],
        )
        for i in indices
    ]

    return examples, (
        similarities,
        indices,
    )


# ============================================================
# Qwen model and generation
# ============================================================

def load_qwen_model(model_path):
    print(
        "Loading Qwen model and tokenizer "
        f"from {model_path}..."
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Qwen model and tokenizer loaded.")

    return model, tokenizer


def build_few_shot_prompt(
    text,
    examples,
):
    system_prompt, user_prompt = generate_ner_prompts(text)

    blocks = []

    for i, (example_text, entities) in enumerate(
        examples,
        start=1,
    ):
        block = (
            f"### Example {i} ###\n"
            f"Input Text:\n"
            f"{example_text}\n"
            f"Output:\n"
            f"{json.dumps(entities, ensure_ascii=False)}"
        )

        blocks.append(block)

    examples_prompt = "\n\n".join(blocks)

    system_prompt += (
        "\n\n"
        "### Retrieved Examples ###\n"
        f"{examples_prompt}"
    )

    return (
        f"{system_prompt}\n\n"
        f"{user_prompt}"
    )


def perform_ner_with_qwen(
    model,
    tokenizer,
    text,
    examples,
    max_input_tokens=4096,
    max_new_tokens=1512,
):
    prompt = build_few_shot_prompt(
        text,
        examples,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
        padding=True,
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    generated_tokens = outputs[0][inputs.input_ids.shape[-1]:]

    return tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    ).strip()


# ============================================================
# Process TEST split
# ============================================================

def process_text_files(
    test_dataset,
    output_dir,
    max_input_tokens,
    max_new_tokens,
    model,
    tokenizer,
    embedder,
    index,
    corpus_texts,
    corpus_entities,
    top_k,
):
    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    print(
        f"Processing {len(test_dataset)} "
        "test documents..."
    )

    for example in test_dataset:
        filename = example["file_name"]

        output_text_path = os.path.join(
            output_dir,
            filename.replace(
                ".txt",
                "_annotated.txt",
            ),
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

        text = " ".join(example["Tokens"])

        examples, retrieval_info = get_similar_examples(
            text,
            embedder,
            index,
            corpus_texts,
            corpus_entities,
            top_k,
        )

        similarities, retrieved_indices = retrieval_info

        print(f"Processing {filename}...")

        print(
            "Retrieved training examples:",
            retrieved_indices,
        )

        print(
            "Similarities:",
            [
                round(score, 4)
                for score in similarities
            ],
        )

        ner_result = perform_ner_with_qwen(
            model=model,
            tokenizer=tokenizer,
            text=text,
            examples=examples,
            max_input_tokens=max_input_tokens,
            max_new_tokens=max_new_tokens,
        )

        with open(
            output_text_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(ner_result)

        print(
            f"Saved: {output_text_path}"
        )


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset_name",
        default=HF_DATASET,
        help="Hugging Face dataset repository.",
    )

    parser.add_argument(
        "--dataset_config",
        default=DATASET_CONFIG,
        help="Hugging Face dataset configuration.",
    )

    parser.add_argument(
        "--index",
        default="ner_embeddings.index",
        help="Output path for FAISS index.",
    )

    parser.add_argument(
        "--embedder",
        default=(
            "intfloat/"
            "multilingual-e5-large"
        ),
        help="Embedding model used for retrieval.",
    )

    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help=(
            "Number of training examples "
            "retrieved for each test document."
        ),
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory for raw Qwen outputs.",
    )

    parser.add_argument(
        "--output_dir_json",
        required=True,
        help=(
            "Directory for extracted JSON "
            "evaluation output."
        ),
    )

    parser.add_argument(
        "--model_name",
        default="Qwen2.5-32B-Instruct",
        help=(
            "Human-readable model name used "
            "in evaluation results."
        ),
    )

    parser.add_argument(
        "--model_path",
        default=DEFAULT_MODEL_PATH,
        help="Local Qwen model path.",
    )

    parser.add_argument(
        "--max_input_tokens",
        type=int,
        default=4096,
        help="Maximum input prompt tokens.",
    )

    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=1512,
        help="Maximum number of generated output tokens.",
    )

    args = parser.parse_args()

    print(
        f"Loading dataset: "
        f"{args.dataset_name}"
    )

    dataset = load_dataset(
        args.dataset_name,
        args.dataset_config,
    )

    print(dataset)

    train_dataset = dataset["train"]
    test_dataset = dataset["test"]

    print(
        f"Training documents for retrieval: "
        f"{len(train_dataset)}"
    )

    print(
        f"Test documents for evaluation: "
        f"{len(test_dataset)}"
    )

    label_list = get_label_list(dataset)

    corpus_texts, corpus_entities = prepare_retrieval_corpus(
        train_dataset,
        label_list,
    )

    print(
        f"Loading embedding model: "
        f"{args.embedder}"
    )

    embedder = SentenceTransformer(args.embedder)

    corpus_embeddings = embed_texts(
        embedder,
        corpus_texts,
    )

    index = build_index(
        corpus_embeddings,
        args.index,
    )

    qwen_model, qwen_tokenizer = load_qwen_model(
        args.model_path
    )

    process_text_files(
        test_dataset=test_dataset,
        output_dir=args.output_dir,
        max_input_tokens=args.max_input_tokens,
        max_new_tokens=args.max_new_tokens,
        model=qwen_model,
        tokenizer=qwen_tokenizer,
        embedder=embedder,
        index=index,
        corpus_texts=corpus_texts,
        corpus_entities=corpus_entities,
        top_k=args.top_k,
    )

    log_dir = os.environ.get("LOG_DIR")

    evaluate_all(
        args.model_name,
        test_dataset,
        args.output_dir,
        args.output_dir_json,
        args.top_k,
        log_dir,
    )

    print("NER processing complete.")


if __name__ == "__main__":
    main()
