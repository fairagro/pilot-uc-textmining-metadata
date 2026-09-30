import os
import json
import csv
import re


# ============================================================
# Label mapping
# ============================================================

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


def get_label_list(dataset):
    """
    Get label names directly from the Hugging Face dataset
    when available.
    """

    try:
        feature = dataset.features["ner_tags"]

        if hasattr(feature, "feature"):
            if hasattr(feature.feature, "names"):
                return feature.feature.names

    except Exception:
        pass

    return LABEL_LIST


# ============================================================
# Reconstruct text and character offsets
# ============================================================

def tokens_to_text_and_offsets(tokens):
    """
    Reconstruct exactly the same text given to the LLM:

        " ".join(tokens)

    Also calculate character offsets for each token.
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

    return "".join(text_parts), offsets


# ============================================================
# Gold BIO -> entity spans
# ============================================================

def bio_to_entities(tokens, ner_tags, label_list):
    """
    Convert the Hugging Face BIO annotations into entity spans.

    Returns:
        [
            {
                "type": "cropSpecies",
                "value": "wheat",
                "start": 25,
                "end": 30
            },
            ...
        ]
    """

    text, offsets = tokens_to_text_and_offsets(tokens)

    entities = []

    current_type = None
    current_start = None
    current_end = None

    def save_entity():
        nonlocal current_type
        nonlocal current_start
        nonlocal current_end

        if current_type is not None:

            entities.append({
                "type": current_type,
                "value": text[
                    current_start:current_end
                ],
                "start": current_start,
                "end": current_end
            })

        current_type = None
        current_start = None
        current_end = None

    for i, tag_id in enumerate(ner_tags):

        label = label_list[tag_id]

        if label == "O":

            save_entity()
            continue

        prefix, entity_type = label.split("-", 1)

        token_start, token_end = offsets[i]

        if prefix == "B":

            save_entity()

            current_type = entity_type
            current_start = token_start
            current_end = token_end

        elif prefix == "I":

            if current_type == entity_type:

                current_end = token_end

            else:
                # Handle malformed orphan I-tag robustly
                save_entity()

                current_type = entity_type
                current_start = token_start
                current_end = token_end

    save_entity()

    return entities


# ============================================================
# Read LLM result
# ============================================================

def extract_prediction_json(file_path):
    """
    Supports both:

    OpenRouter:
        {
          "choices": [{
            "message": {
              "content": "{...}"
            }
          }]
        }

    and direct JSON model outputs.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        raw = file.read().strip()

    if not raw:
        return None

    try:
        data = json.loads(raw)

    except json.JSONDecodeError:
        data = raw

    # OpenRouter format
    if isinstance(data, dict) and "choices" in data:

        try:
            content = (
                data["choices"][0]
                ["message"]
                ["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ):
            return None

    # Already prediction JSON
    elif isinstance(data, dict):

        return data

    else:
        content = str(data)

    content = content.strip()

    # Remove ```json fences
    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    try:
        return json.loads(content)

    except json.JSONDecodeError:

        # Try extracting JSON object from surrounding text
        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end > start:

            try:
                return json.loads(
                    content[start:end + 1]
                )

            except json.JSONDecodeError:
                pass

    return None


# ============================================================
# Prediction JSON -> flat entity list
# ============================================================

def extract_predicted_entities(prediction):
    """
    Convert:

    {
      "Crops": [
        {
          "cropSpecies": {
            "value": "wheat",
            "span": [10, 15]
          }
        }
      ]
    }

    into:

    [
      {
        "type": "cropSpecies",
        "value": "wheat",
        "start": 10,
        "end": 15
      }
    ]
    """

    entities = []

    if not isinstance(prediction, dict):
        return entities

    for category_entities in prediction.values():

        if not isinstance(category_entities, list):
            continue

        for entity_object in category_entities:

            if not isinstance(entity_object, dict):
                continue

            for entity_type, entity_data in entity_object.items():

                if not isinstance(entity_data, dict):
                    continue

                span = entity_data.get("span")

                if (
                    not isinstance(span, list)
                    or len(span) != 2
                ):
                    continue

                try:
                    start = int(span[0])
                    end = int(span[1])

                except (TypeError, ValueError):
                    continue

                if start < 0 or end <= start:
                    continue

                entities.append({
                    "type": entity_type,
                    "value": entity_data.get(
                        "value",
                        ""
                    ),
                    "start": start,
                    "end": end
                })

    return entities


# ============================================================
# Matching functions
# ============================================================

def exact_match(gold, pred):
    """
    Same entity type and identical character span.
    """

    return (
        gold["type"] == pred["type"]
        and gold["start"] == pred["start"]
        and gold["end"] == pred["end"]
    )


def spans_overlap(gold, pred):
    """
    Same entity type and any character-span overlap.
    """

    if gold["type"] != pred["type"]:
        return False

    return (
        gold["start"] < pred["end"]
        and pred["start"] < gold["end"]
    )


def overlap_length(gold, pred):
    """
    Number of overlapping characters.
    """

    return max(
        0,
        min(gold["end"], pred["end"])
        - max(gold["start"], pred["start"])
    )


# ============================================================
# Count exact matches
# ============================================================

def count_exact_matches(gold_entities, pred_entities):
    """
    One-to-one exact matching.
    """

    matched_gold = set()
    matched_pred = set()

    for p_idx, pred in enumerate(pred_entities):

        for g_idx, gold in enumerate(gold_entities):

            if g_idx in matched_gold:
                continue

            if exact_match(gold, pred):

                matched_gold.add(g_idx)
                matched_pred.add(p_idx)

                break

    tp = len(matched_pred)

    fp = len(pred_entities) - tp
    fn = len(gold_entities) - tp

    return tp, fp, fn


# ============================================================
# Count partial matches
# ============================================================

def count_partial_matches(gold_entities, pred_entities):
    """
    Partial matching:

    - entity type must be identical
    - character spans must overlap
    - each gold entity can match only one prediction
    - each prediction can match only one gold entity

    If multiple possible overlaps exist, the pair with the
    greatest overlap is matched first.
    """

    candidates = []

    for g_idx, gold in enumerate(gold_entities):

        for p_idx, pred in enumerate(pred_entities):

            if spans_overlap(gold, pred):

                overlap = overlap_length(
                    gold,
                    pred
                )

                candidates.append(
                    (
                        overlap,
                        g_idx,
                        p_idx
                    )
                )

    # Prefer the strongest overlap
    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    matched_gold = set()
    matched_pred = set()

    for overlap, g_idx, p_idx in candidates:

        if g_idx in matched_gold:
            continue

        if p_idx in matched_pred:
            continue

        matched_gold.add(g_idx)
        matched_pred.add(p_idx)

    tp = len(matched_pred)

    fp = len(pred_entities) - tp
    fn = len(gold_entities) - tp

    return tp, fp, fn


# ============================================================
# Calculate P / R / F1
# ============================================================

def calculate_metrics(tp, fp, fn):

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn
    }


# ============================================================
# Main evaluation
# ============================================================

def evaluate_all(
    model_name,
    test_dataset,
    output_dir,
    output_dir_json=None,
    top_k=None,
    log_dir=None
):
    """
    Calculate exact and partial entity-level NER scores.

    Exact:
        Same entity type AND identical character span.

    Partial:
        Same entity type AND overlapping character span.

    Metrics are calculated:
        - for every entity class
        - overall across all classes
    """

    label_list = get_label_list(
        test_dataset
    )

    entity_types = sorted({
        label.split("-", 1)[1]
        for label in label_list
        if label != "O"
    })

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    exact_counts = {
        entity_type: {
            "tp": 0,
            "fp": 0,
            "fn": 0
        }
        for entity_type in entity_types
    }

    partial_counts = {
        entity_type: {
            "tp": 0,
            "fp": 0,
            "fn": 0
        }
        for entity_type in entity_types
    }

    processed_documents = 0
    missing_documents = 0
    invalid_documents = 0

    # ========================================================
    # Evaluate each document
    # ========================================================

    for example in test_dataset:

        filename = example["file_name"]

        output_filename = filename.replace(
            ".txt",
            "_annotated.txt"
        )

        prediction_path = os.path.join(
            output_dir,
            output_filename
        )

        # ----------------------------------------------------
        # Missing prediction
        # ----------------------------------------------------

        if not os.path.exists(
            prediction_path
        ):

            print(
                f"Missing prediction: {filename}"
            )

            missing_documents += 1
            continue

        # ----------------------------------------------------
        # Gold entities
        # ----------------------------------------------------

        gold_entities = bio_to_entities(
            example["Tokens"],
            example["ner_tags"],
            label_list
        )

        # ----------------------------------------------------
        # Predicted entities
        # ----------------------------------------------------

        prediction = extract_prediction_json(
            prediction_path
        )

        if prediction is None:

            print(
                f"Invalid prediction: {filename}"
            )

            invalid_documents += 1
            continue

        pred_entities = (
            extract_predicted_entities(
                prediction
            )
        )

        # ====================================================
        # Evaluate each entity type independently
        # ====================================================

        for entity_type in entity_types:

            gold_class = [
                entity
                for entity in gold_entities
                if entity["type"] == entity_type
            ]

            pred_class = [
                entity
                for entity in pred_entities
                if entity["type"] == entity_type
            ]

            # Exact
            tp, fp, fn = count_exact_matches(
                gold_class,
                pred_class
            )

            exact_counts[entity_type]["tp"] += tp
            exact_counts[entity_type]["fp"] += fp
            exact_counts[entity_type]["fn"] += fn

            # Partial
            tp, fp, fn = count_partial_matches(
                gold_class,
                pred_class
            )

            partial_counts[entity_type]["tp"] += tp
            partial_counts[entity_type]["fp"] += fp
            partial_counts[entity_type]["fn"] += fn

        processed_documents += 1

    # ========================================================
    # Calculate per-class metrics
    # ========================================================

    per_class = {}

    for entity_type in entity_types:

        exact = calculate_metrics(
            exact_counts[entity_type]["tp"],
            exact_counts[entity_type]["fp"],
            exact_counts[entity_type]["fn"]
        )

        partial = calculate_metrics(
            partial_counts[entity_type]["tp"],
            partial_counts[entity_type]["fp"],
            partial_counts[entity_type]["fn"]
        )

        per_class[entity_type] = {
            "exact": exact,
            "partial": partial
        }

    # ========================================================
    # Overall MICRO metrics
    # ========================================================

    exact_tp = sum(
        values["tp"]
        for values in exact_counts.values()
    )

    exact_fp = sum(
        values["fp"]
        for values in exact_counts.values()
    )

    exact_fn = sum(
        values["fn"]
        for values in exact_counts.values()
    )

    partial_tp = sum(
        values["tp"]
        for values in partial_counts.values()
    )

    partial_fp = sum(
        values["fp"]
        for values in partial_counts.values()
    )

    partial_fn = sum(
        values["fn"]
        for values in partial_counts.values()
    )

    overall_exact = calculate_metrics(
        exact_tp,
        exact_fp,
        exact_fn
    )

    overall_partial = calculate_metrics(
        partial_tp,
        partial_fp,
        partial_fn
    )

    # ========================================================
    # Macro F1
    # ========================================================

    exact_macro_f1 = sum(
        per_class[c]["exact"]["f1"]
        for c in entity_types
    ) / len(entity_types)

    partial_macro_f1 = sum(
        per_class[c]["partial"]["f1"]
        for c in entity_types
    ) / len(entity_types)

    # ========================================================
    # Result object
    # ========================================================

    results = {
        "model": model_name,
        "top_k": top_k,

        "documents": {
            "processed": processed_documents,
            "missing": missing_documents,
            "invalid": invalid_documents
        },

        "overall": {
            "exact": overall_exact,
            "partial": overall_partial,
            "exact_macro_f1": exact_macro_f1,
            "partial_macro_f1": partial_macro_f1
        },

        "per_class": per_class
    }

    # ========================================================
    # Print table
    # ========================================================

    print()
    print("=" * 115)

    print(
        f"NER evaluation: {model_name}"
    )

    print("=" * 115)

    print(
        f"{'Class':30s} "
        f"{'Exact P':>9s} "
        f"{'Exact R':>9s} "
        f"{'Exact F1':>9s} "
        f"{'Partial P':>10s} "
        f"{'Partial R':>10s} "
        f"{'Partial F1':>10s}"
    )

    print("-" * 115)

    for entity_type in entity_types:

        exact = per_class[
            entity_type
        ]["exact"]

        partial = per_class[
            entity_type
        ]["partial"]

        print(
            f"{entity_type:30s} "
            f"{exact['precision']:9.4f} "
            f"{exact['recall']:9.4f} "
            f"{exact['f1']:9.4f} "
            f"{partial['precision']:10.4f} "
            f"{partial['recall']:10.4f} "
            f"{partial['f1']:10.4f}"
        )

    print("-" * 115)

    print(
        f"{'OVERALL MICRO':30s} "
        f"{overall_exact['precision']:9.4f} "
        f"{overall_exact['recall']:9.4f} "
        f"{overall_exact['f1']:9.4f} "
        f"{overall_partial['precision']:10.4f} "
        f"{overall_partial['recall']:10.4f} "
        f"{overall_partial['f1']:10.4f}"
    )

    print()

    print(
        f"Exact macro F1:   "
        f"{exact_macro_f1:.4f}"
    )

    print(
        f"Partial macro F1: "
        f"{partial_macro_f1:.4f}"
    )

    print(
        f"Documents processed: "
        f"{processed_documents}"
    )

    print(
        f"Missing predictions: "
        f"{missing_documents}"
    )

    print(
        f"Invalid predictions: "
        f"{invalid_documents}"
    )

    # ========================================================
    # Save JSON + CSV
    # ========================================================

    if output_dir_json:

        os.makedirs(
            output_dir_json,
            exist_ok=True
        )

        safe_model_name = (
            model_name
            .replace("/", "_")
            .replace(" ", "_")
        )

        if top_k is not None:

            base_name = (
                f"{safe_model_name}_"
                f"{top_k}shot_metrics"
            )

        else:

            base_name = (
                f"{safe_model_name}_metrics"
            )

        # JSON
        json_path = os.path.join(
            output_dir_json,
            f"{base_name}.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=2
            )

        # CSV
        csv_path = os.path.join(
            output_dir_json,
            f"{base_name}.csv"
        )

        with open(
            csv_path,
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "class",
                "exact_precision",
                "exact_recall",
                "exact_f1",
                "partial_precision",
                "partial_recall",
                "partial_f1",
                "gold_entities"
            ])

            for entity_type in entity_types:

                exact = per_class[
                    entity_type
                ]["exact"]

                partial = per_class[
                    entity_type
                ]["partial"]

                writer.writerow([
                    entity_type,
                    exact["precision"],
                    exact["recall"],
                    exact["f1"],
                    partial["precision"],
                    partial["recall"],
                    partial["f1"],
                    exact["tp"] + exact["fn"]
                ])

            writer.writerow([
                "OVERALL_MICRO",
                overall_exact["precision"],
                overall_exact["recall"],
                overall_exact["f1"],
                overall_partial["precision"],
                overall_partial["recall"],
                overall_partial["f1"],
                exact_tp + exact_fn
            ])

        print(
            f"\nSaved metrics to: {json_path}"
        )

        print(
            f"Saved metrics to: {csv_path}"
        )

    return results