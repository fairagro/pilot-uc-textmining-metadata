import os
import sys
import json
import argparse
from typing import List, Any

import faiss
import numpy as np
import requests

from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

sys.path.append(os.path.abspath(".."))

from code.Experiments.generate_ner_prompt import generate_ner_prompts
from code.Experiments.evaluation import evaluate_all
load_dotenv()


# ============================================================
# Configuration
# ============================================================

HF_DATASET = (
    "IT-ZBMED/"
    "Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
)

DATASET_CONFIG = "doc_split"


# Fallback label mapping in case the Hugging Face feature does
# not expose the ClassLabel names directly.
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
    "I-soilBulkDensity"
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
    """
    Reconstruct the document exactly as:

        " ".join(tokens)

    while also calculating the character offsets of every token.

    This makes the character spans in the retrieved demonstrations
    consistent with the text that is actually shown to the LLM.
    """

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

    text = "".join(text_parts)

    return text, offsets


# ============================================================
# Convert BIO annotations into prompt JSON
# ============================================================

def bio_to_json(tokens, ner_tags, label_list):
    """
    Convert BIO annotations from the Hugging Face dataset into
    the JSON structure expected by generate_ner_prompts().
    """

    text, offsets = tokens_to_text_and_offsets(tokens)

    result = {
        "Crops": [],
        "Soil": [],
        "Location": [],
        "Time Statement": []
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

        if category is None:
            current_entity = None
            current_start = None
            current_end = None
            return

        value = text[current_start:current_end]

        result[category].append({
            current_entity: {
                "value": value,
                "span": [
                    current_start,
                    current_end
                ]
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

            # Normal continuation of the current entity
            if current_entity == entity_type:
                current_end = end

            else:
                # Robust handling of an orphan/mismatched I-tag.
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
    """
    Try to retrieve the BIO label names from the Hugging Face
    dataset itself. Fall back to LABEL_LIST if necessary.
    """

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

    print(
        "Using predefined fallback LABEL_LIST."
    )

    return LABEL_LIST


# ============================================================
# Prepare retrieval corpus from TRAIN split
# ============================================================

def prepare_retrieval_corpus(
    train_dataset,
    label_list
):
    """
    Convert every training document into:

        full text
        gold JSON entities

    These are used exclusively as retrieval demonstrations.
    """

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
            label_list
        )

        corpus_texts.append(text)
        corpus_entities.append(entities)

    print(
        f"Retrieval corpus contains "
        f"{len(corpus_texts)} documents."
    )

    return corpus_texts, corpus_entities


# ============================================================
# Embeddings
# ============================================================

def embed_texts(
    embedder,
    texts: List[str],
    batch_size: int = 64
):
    embeddings = embedder.encode(
        texts,
        convert_to_numpy=True,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings.astype("float32")


# ============================================================
# Build FAISS index
# ============================================================

def build_index(
    embeddings: np.ndarray,
    index_path: str
):
    dimension = embeddings.shape[1]

    # Inner product on normalized vectors = cosine similarity
    index = faiss.IndexFlatIP(
        dimension
    )

    # Embeddings are already normalized, but keeping this
    # guarantees normalization before indexing.
    faiss.normalize_L2(
        embeddings
    )

    index.add(
        embeddings
    )

    if index_path:
        faiss.write_index(
            index,
            index_path
        )

        print(
            f"FAISS index saved to: "
            f"{index_path}"
        )

    return index


# ============================================================
# Retrieve nearest training examples
# ============================================================

def get_similar_examples(
    query_text: str,
    embedder,
    index,
    corpus_texts: List[str],
    corpus_entities: List[Any],
    top_k: int = 5
):
    query_embedding = embedder.encode(
        [query_text],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    actual_k = min(
        top_k,
        len(corpus_texts)
    )

    similarities, indices = index.search(
        query_embedding,
        actual_k
    )

    indices = indices[0].tolist()
    similarities = similarities[0].tolist()

    examples = [
        (
            corpus_texts[i],
            corpus_entities[i]
        )
        for i in indices
    ]

    return examples, (
        similarities,
        indices
    )


# ============================================================
# Perform NER
# ============================================================

def perform_ner(
    text,
    max_length,
    examples,
    model
):
    """
    Perform retrieval-augmented few-shot NER.

    The base zero-shot prompt is generated first, after which
    the top-k retrieved training examples are appended to the
    system prompt.
    """

    system_prompt, user_prompt = generate_ner_prompts(
        text
    )

    blocks = []

    for i, (example_text, entities) in enumerate(
        examples,
        start=1
    ):

        block = (
            f"### Example {i} ###\n"
            f"Input Text:\n"
            f"{example_text}\n"
            f"Output:\n"
            f"{json.dumps(entities, ensure_ascii=False)}"
        )

        blocks.append(block)

    examples_prompt = "\n\n".join(
        blocks
    )

    system_prompt += (
        "\n\n"
        "### Retrieved Examples ###\n"
        f"{examples_prompt}"
    )

    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set."
        )

    response = requests.post(
        url=(
            "https://openrouter.ai/"
            "api/v1/chat/completions"
        ),
        headers={
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": (
                "application/json"
            )
        },
        data=json.dumps({
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "provider": {
                "sort": "price"
            },
            "temperature": 0.7,
            "max_tokens": max_length,
            "top_p": 0.90
        }),
        timeout=300
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# Process TEST split
# ============================================================

def process_text_files(
    test_dataset,
    output_dir,
    max_length,
    embedder,
    index,
    corpus_texts,
    corpus_entities,
    top_k,
    model
):
    """
    Process only the Hugging Face TEST split.

    Retrieval candidates always come exclusively from TRAIN.
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

        output_text_path = os.path.join(
            output_dir,
            filename.replace(
                ".txt",
                "_annotated.txt"
            )
        )

        # ----------------------------------------------------
        # Skip already completed documents
        # ----------------------------------------------------

        if os.path.exists(
            output_text_path
        ):

            try:

                with open(
                    output_text_path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(
                        file
                    )

                content = (
                    data
                    .get(
                        "choices",
                        [{}]
                    )[0]
                    .get(
                        "message",
                        {}
                    )
                    .get(
                        "content"
                    )
                )

                if (
                    content
                    and content.strip()
                ):

                    print(
                        f"Skipping {filename} "
                        "(already processed)."
                    )

                    continue

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                IndexError
            ):

                print(
                    f"Existing result for "
                    f"{filename} is invalid. "
                    "Reprocessing..."
                )

        # ----------------------------------------------------
        # Reconstruct test document
        # ----------------------------------------------------

        text = " ".join(
            example["Tokens"]
        )

        # ----------------------------------------------------
        # Retrieve examples exclusively from TRAIN
        # ----------------------------------------------------

        examples, retrieval_info = (
            get_similar_examples(
                text,
                embedder,
                index,
                corpus_texts,
                corpus_entities,
                top_k
            )
        )

        similarities, retrieved_indices = (
            retrieval_info
        )

        print(
            f"Processing {filename}..."
        )

        print(
            "Retrieved training examples:",
            retrieved_indices
        )

        print(
            "Similarities:",
            [
                round(score, 4)
                for score in similarities
            ]
        )

        # ----------------------------------------------------
        # NER
        # ----------------------------------------------------

        ner_result = perform_ner(
            text,
            max_length,
            examples,
            model
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        with open(
            output_text_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                ner_result,
                file,
                ensure_ascii=False,
                indent=2
            )

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
        help=(
            "Hugging Face dataset repository."
        )
    )

    parser.add_argument(
        "--dataset_config",
        default=DATASET_CONFIG,
        help=(
            "Hugging Face dataset configuration."
        )
    )

    parser.add_argument(
        "--index",
        default="ner_embeddings.index",
        help=(
            "Output path for FAISS index."
        )
    )

    parser.add_argument(
        "--embedder",
        default=(
            "intfloat/"
            "multilingual-e5-large"
        ),
        help=(
            "Embedding model used for retrieval."
        )
    )

    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help=(
            "Number of training examples "
            "retrieved for each test document."
        )
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help=(
            "Directory for raw LLM outputs."
        )
    )

    parser.add_argument(
        "--output_dir_json",
        required=True,
        help=(
            "Directory for extracted JSON "
            "evaluation output."
        )
    )

    parser.add_argument(
        "--model_name",
        required=True,
        help=(
            "Human-readable model name used "
            "in evaluation results."
        )
    )

    parser.add_argument(
        "--model",
        default=(
            "deepseek/"
            "deepseek-chat-v3-0324"
        ),
        help=(
            "OpenRouter model identifier."
        )
    )

    parser.add_argument(
        "--max_length",
        type=int,
        default=1512,
        help=(
            "Maximum number of output tokens."
        )
    )

    args = parser.parse_args()


    # ========================================================
    # Load Hugging Face dataset
    # ========================================================

    print(
        f"Loading dataset: "
        f"{args.dataset_name}"
    )

    dataset = load_dataset(
        args.dataset_name,
        args.dataset_config
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


    # ========================================================
    # Convert TRAIN annotations to retrieval demonstrations
    # ========================================================

    label_list = get_label_list(
        dataset
    )

    corpus_texts, corpus_entities = (
        prepare_retrieval_corpus(
            train_dataset,
            label_list
        )
    )


    # ========================================================
    # Load embedding model
    # ========================================================

    print(
        f"Loading embedding model: "
        f"{args.embedder}"
    )

    embedder = SentenceTransformer(
        args.embedder
    )


    # ========================================================
    # Encode TRAIN documents
    # ========================================================

    corpus_embeddings = embed_texts(
        embedder,
        corpus_texts
    )


    # ========================================================
    # Build FAISS retrieval index
    # ========================================================

    index = build_index(
        corpus_embeddings,
        args.index
    )


    # ========================================================
    # Annotate TEST split
    # ========================================================

    # ========================================================

    process_text_files(
        test_dataset=test_dataset,
        output_dir=args.output_dir,
        max_length=args.max_length,
        embedder=embedder,
        index=index,
        corpus_texts=corpus_texts,
        corpus_entities=corpus_entities,
        top_k=args.top_k,
        model=args.model
    )

    # ========================================================
    # Evaluation
    # ========================================================

    log_dir = os.environ.get(
        "LOG_DIR"
    )

    evaluate_all(
        args.model_name,
        test_dataset,
        args.output_dir,
        args.output_dir_json,
        args.top_k,
        log_dir
    )

    print(
        "NER processing complete."
    )


if __name__ == "__main__":
    main()
