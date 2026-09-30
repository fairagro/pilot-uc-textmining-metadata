import os
import numpy as np
import wandb
import optuna
import evaluate

from datasets import DatasetDict, load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)


# ============================================================
# Configuration
# ============================================================

DATASET_NAME = (
    "IT-ZBMED/"
    "Agriculture_NER_Dataset_for_FAIR_Metadata_Enrichment"
)

DATASET_CONFIG = "sentence_split"

VALIDATION_FRACTION = 0.10
SEED = 42
MAX_LENGTH = 512

# Keep True to reproduce the behavior of the original script:
# all subtokens receive the word's NER label.
LABEL_ALL_SUBTOKENS = True


# ============================================================
# Label mapping
# ============================================================

label_list = [
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

label_to_id = {
    label: i
    for i, label in enumerate(label_list)
}

id_to_label = {
    i: label
    for i, label in enumerate(label_list)
}


# These are initialized later after the checkpoint is selected
tokenizer = None
seqeval = None


# ============================================================
# Tokenization & label alignment
# ============================================================

def tokenize_and_align_labels(example):
    tokenized_inputs = tokenizer(
        example["tokens"],
        truncation=True,
        is_split_into_words=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )

    labels = []

    word_ids = tokenized_inputs.word_ids()
    previous_word_idx = None

    for word_idx in word_ids:

        if word_idx is None:
            # Special tokens
            labels.append(-100)

        elif word_idx != previous_word_idx:
            # First subtoken of a word
            labels.append(
                example["ner_tags"][word_idx]
            )

        else:
            # Additional subtokens of the same word
            if LABEL_ALL_SUBTOKENS:
                labels.append(
                    example["ner_tags"][word_idx]
                )
            else:
                labels.append(-100)

        previous_word_idx = word_idx

    tokenized_inputs["labels"] = labels

    return tokenized_inputs


# ============================================================
# Align predictions for metrics
# ============================================================

def align_predictions(predictions, label_ids):

    preds = np.argmax(
        predictions,
        axis=2
    )

    batch_size, seq_len = preds.shape

    out_label_list = [
        [] for _ in range(batch_size)
    ]

    out_pred_list = [
        [] for _ in range(batch_size)
    ]

    for i in range(batch_size):

        for j in range(seq_len):

            if label_ids[i][j] != -100:

                out_label_list[i].append(
                    label_list[label_ids[i][j]]
                )

                out_pred_list[i].append(
                    label_list[preds[i][j]]
                )

    return out_pred_list, out_label_list


# ============================================================
# Compute metrics with seqeval
# ============================================================

def compute_metrics(p):

    predictions, label_ids = p

    preds, labels = align_predictions(
        predictions,
        label_ids
    )

    results = seqeval.compute(
        predictions=preds,
        references=labels
    )

    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }


# ============================================================
# Create validation split
# ============================================================

def create_validation_split(
    dataset,
    validation_fraction=0.10,
    seed=42
):
    """
    The Hugging Face dataset contains train and test splits,
    but no validation split.

    Validation documents are selected from the training set
    based on file_name so that sentences from the same document
    cannot occur in both training and validation.
    """

    train_dataset = dataset["train"]

    file_names = np.array(
        sorted(set(train_dataset["file_name"]))
    )

    rng = np.random.default_rng(seed)
    rng.shuffle(file_names)

    number_validation_files = max(
        1,
        int(
            round(
                len(file_names)
                * validation_fraction
            )
        )
    )

    validation_files = set(
        file_names[:number_validation_files]
    )

    print(
        f"Total training documents: "
        f"{len(file_names)}"
    )

    print(
        f"Validation documents: "
        f"{len(validation_files)}"
    )

    new_train_dataset = train_dataset.filter(
        lambda example:
        example["file_name"]
        not in validation_files
    )

    validation_dataset = train_dataset.filter(
        lambda example:
        example["file_name"]
        in validation_files
    )

    return DatasetDict({
        "train": new_train_dataset,
        "validation": validation_dataset,
        "test": dataset["test"],
    })


# ============================================================
# Tokenizer loader
# ============================================================

def load_model_tokenizer(model_checkpoint):
    """
    Load a fast tokenizer for any compatible Hugging Face
    encoder checkpoint.

    Some RoBERTa tokenizers require add_prefix_space=True
    when using pre-tokenized words.
    """

    tokenizer = AutoTokenizer.from_pretrained(
        model_checkpoint,
        use_fast=True
    )

    if not tokenizer.is_fast:
        raise ValueError(
            f"{model_checkpoint} did not load a fast tokenizer. "
            "A fast tokenizer is required because word_ids() "
            "is used for NER label alignment."
        )

    # Test whether pre-tokenized input is supported directly.
    try:
        tokenizer(
            ["test"],
            is_split_into_words=True
        )

    except (AssertionError, ValueError) as error:

        if "add_prefix_space" in str(error):

            tokenizer = AutoTokenizer.from_pretrained(
                model_checkpoint,
                use_fast=True,
                add_prefix_space=True
            )

        else:
            raise error

    return tokenizer


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Login to W&B
    # --------------------------------------------------------

    # Uses WANDB_API_KEY environment variable if available.
    # Do not hard-code the API key in the script.
    wandb.login()


    # --------------------------------------------------------
    # Load Hugging Face dataset
    # --------------------------------------------------------

    dataset = load_dataset(
        DATASET_NAME,
        DATASET_CONFIG
    )

    print(dataset)

    # The Hugging Face dataset uses "Tokens".
    # The original code expects "tokens".
    if "Tokens" in dataset["train"].column_names:
        dataset = dataset.rename_column(
            "Tokens",
            "tokens"
        )

    # Add validation split while keeping documents separate.
    dataset = create_validation_split(
        dataset,
        validation_fraction=VALIDATION_FRACTION,
        seed=SEED
    )

    print("\nDataset after validation split:")
    print(dataset)


    # --------------------------------------------------------
    # MODEL CHECKPOINT
    # --------------------------------------------------------
    #
    # This is now the only line that needs to change when
    # switching between pretrained models.
    #

    model_checkpoint = "xlm-roberta-large"

    # Other examples:
    #
    # model_checkpoint = "recobo/agriculture-bert-uncased"
    #
    # model_checkpoint = "allenai/scibert_scivocab_uncased"


    # Convert "/" in Hugging Face model names so that the
    # checkpoint name can safely be used in directory names.
    safe_model_name = model_checkpoint.replace("/", "__")


    # --------------------------------------------------------
    # Load tokenizer
    # --------------------------------------------------------

    tokenizer = load_model_tokenizer(
        model_checkpoint
    )

    print(
        f"\nUsing model: {model_checkpoint}"
    )

    print(
        f"Tokenizer: "
        f"{tokenizer.__class__.__name__}"
    )


    # --------------------------------------------------------
    # Tokenize dataset
    # --------------------------------------------------------

    original_columns = dataset["train"].column_names

    tokenized_dataset = dataset.map(
        tokenize_and_align_labels,
        remove_columns=original_columns
    )


    # --------------------------------------------------------
    # Load metric
    # --------------------------------------------------------

    seqeval = evaluate.load("seqeval")


    # --------------------------------------------------------
    # Optuna hyperparameter search space
    # --------------------------------------------------------

    def optuna_hp_space(trial):

        return {
            "learning_rate": trial.suggest_float(
                "learning_rate",
                1e-5,
                5e-5,
                log=True
            ),

            "num_train_epochs": trial.suggest_int(
                "num_train_epochs",
                3,
                30
            ),

            "per_device_train_batch_size":
                trial.suggest_categorical(
                    "per_device_train_batch_size",
                    [8, 16, 32]
                ),

            "weight_decay": trial.suggest_float(
                "weight_decay",
                0.0,
                0.3
            ),
        }


    # --------------------------------------------------------
    # Model initialization
    # --------------------------------------------------------

    def model_init():

        return AutoModelForTokenClassification.from_pretrained(
            model_checkpoint,
            num_labels=len(label_list),
            label2id=label_to_id,
            id2label=id_to_label,
            ignore_mismatched_sizes=True
        )


    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    base_output_dir = (
        f"/code/Experiments/results/"
        f"model_{safe_model_name}"
    )


    # --------------------------------------------------------
    # Training arguments for Optuna
    # --------------------------------------------------------

    training_args = TrainingArguments(

        output_dir=os.path.join(
            base_output_dir,
            "optuna"
        ),

        eval_strategy="epoch",
        save_strategy="epoch",

        logging_dir=os.path.join(
            base_output_dir,
            "logs_optuna"
        ),

        run_name=(
            f"{safe_model_name}_optuna"
        ),

        metric_for_best_model="f1",
        greater_is_better=True,

        load_best_model_at_end=True,

        seed=SEED,
        data_seed=SEED,

        report_to="wandb",
    )


    # --------------------------------------------------------
    # Trainer for hyperparameter search
    # --------------------------------------------------------

    trainer = Trainer(

        model_init=model_init,

        args=training_args,

        train_dataset=(
            tokenized_dataset["train"]
        ),

        eval_dataset=(
            tokenized_dataset["validation"]
        ),

        tokenizer=tokenizer,

        compute_metrics=compute_metrics,

        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=3
            )
        ]
    )


    # --------------------------------------------------------
    # Run Optuna search
    # --------------------------------------------------------

    best_trial = trainer.hyperparameter_search(

        direction="maximize",

        hp_space=optuna_hp_space,

        backend="optuna",

        n_trials=10
    )

    print("\nBest trial:")
    print(best_trial)


    # --------------------------------------------------------
    # Retrain using the best hyperparameters
    # --------------------------------------------------------

    best_args = TrainingArguments(

        output_dir=os.path.join(
            base_output_dir,
            "best_model"
        ),

        eval_strategy="epoch",
        save_strategy="epoch",

        logging_dir=os.path.join(
            base_output_dir,
            "logs_best"
        ),

        run_name=safe_model_name,

        learning_rate=(
            best_trial.hyperparameters[
                "learning_rate"
            ]
        ),

        num_train_epochs=(
            best_trial.hyperparameters[
                "num_train_epochs"
            ]
        ),

        per_device_train_batch_size=(
            best_trial.hyperparameters[
                "per_device_train_batch_size"
            ]
        ),

        weight_decay=(
            best_trial.hyperparameters[
                "weight_decay"
            ]
        ),

        metric_for_best_model="f1",

        greater_is_better=True,

        load_best_model_at_end=True,

        seed=SEED,
        data_seed=SEED,

        report_to="wandb",
    )


    trainer = Trainer(

        model_init=model_init,

        args=best_args,

        train_dataset=(
            tokenized_dataset["train"]
        ),

        eval_dataset=(
            tokenized_dataset["validation"]
        ),

        tokenizer=tokenizer,

        compute_metrics=compute_metrics,

        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=3
            )
        ]
    )


    # --------------------------------------------------------
    # Train final model
    # --------------------------------------------------------

    trainer.train()


    # --------------------------------------------------------
    # Inspect validation predictions
    # --------------------------------------------------------

    outputs = trainer.predict(
        tokenized_dataset["validation"]
    )

    preds, labels = align_predictions(
        outputs.predictions,
        outputs.label_ids
    )

    for i in range(
        min(3, len(preds))
    ):

        print("Pred:", preds[i])
        print("Gold:", labels[i])
        print()


    # --------------------------------------------------------
    # Final test evaluation
    # --------------------------------------------------------

    results = trainer.predict(
        tokenized_dataset["test"]
    )

    print("\nFinal test results:")
    print(results.metrics)