import json
import pandas as pd
from cassis import *
import spacy
nlp = spacy.load("en_core_web_sm")

def cas_sentence_to_bio(cas, sentence, annotation_types= [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ]):
    """
    This function takes the cas file, one of its sentences and the annotation classes. It converts the sentence into a list of tokens 
    and matches them with thier BIO format labels
    Parameters:
        cas : A cas object that represents the document 
        sentence: A cas sentence object
        annotation_types: The annotation classes according to their definitions in the cas typesystem file
    Returns:
        tokens: Sentence tokenized into a list words
        labels: Correspoinding BIO labels as a list of strings
    """
    text = cas.sofa_string
    sentence_text = text[sentence.begin:sentence.end]
    doc = nlp(sentence_text)
    tokens = [token.text for token in doc]
    labels = ["O"] * len(tokens)
    sen_begin = sentence.begin
    sen_end = sentence.end
    for type_name in annotation_types:
        for ann in cas.select(type_name):
            begin = ann.begin
            end = ann.end
            if begin <= sen_end and begin >= sen_begin and end >= sen_begin and end <= sen_end:
                # Get label name based on available features
                label = None
                for feat in ann.type.all_features:
                    if feat.name != "sofa" and feat.name != "begin" and feat.name != "end" and hasattr(ann, feat.name):
                        val = getattr(ann, feat.name)
                        if val:
                            label = val
                            break

                if not label:
                    label = type_name.split(".")[-1]  # fallback to type name

                for i, token in enumerate(doc):
                    token_start = token.idx + sen_begin
                    token_end = token_start + len(token)

                    if token_start >= begin and token_end <= end:
                        labels[i] = f"B-{label}" if token_start == begin else f"I-{label}"

    return tokens, labels


def cas_files_to_bio(cas, annotation_types= [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ]):
    """
    This function takes the cas fileand the annotation classes. It converts the file into a list of tokens 
    and matches them with thier BIO format labels
    Parameters:
        cas : A cas object that represents the document 
        annotation_types: The annotation classes according to their definitions in the cas typesystem file
    Returns:
        tokens: Sentence tokenized into a list words
        labels: Correspoinding BIO labels as a list of strings
    """
    text = cas.sofa_string
    doc = nlp(text)
    tokens = [token.text for token in doc]
    labels = ["O"] * len(tokens)
    sen_begin = 0
    sen_end = len(text)-1
    for type_name in annotation_types:
        for ann in cas.select(type_name):
            begin = ann.begin
            end = ann.end
            if begin <= sen_end and begin >= sen_begin and end >= sen_begin and end <= sen_end:
                # Get label name based on available features
                label = None
                for feat in ann.type.all_features:
                    if feat.name != "sofa" and feat.name != "begin" and feat.name != "end" and hasattr(ann, feat.name):
                        val = getattr(ann, feat.name)
                        if val:
                            label = val
                            break

                if not label:
                    label = type_name.split(".")[-1]  # fallback to type name

                for i, token in enumerate(doc):
                    if token.idx >= begin and (token.idx + len(token)) <= end:
                        labels[i] = f"B-{label}" if token.idx == begin else f"I-{label}"

    return tokens, labels


def cas_to_bio(cas, annotation_types):
    """
    This function takes the cas file and the annotation classes. It converts the cas file into a list of tokens 
    and matches them with thier BIO format labels
    Parameters:
        cas : A cas object that represents the document 
        annotation_types: The annotation classes according to their definitions in the cas typesystem file
    Returns:
        tokens: Sentence tokenized into a list words
        labels: Correspoinding BIO labels as a list of strings
    """
    text = cas.sofa_string
    doc = nlp(text)
    tokens = [token.text for token in doc]
    labels = ["O"] * len(tokens)

    for type_name in annotation_types:
        for ann in cas.select(type_name):
            begin = ann.begin
            end = ann.end

            # Get label name based on available features
            label = None
            for feat in ann.type.all_features:
                if feat.name != "sofa" and feat.name != "begin" and feat.name != "end" and hasattr(ann, feat.name):
                    val = getattr(ann, feat.name)
                    if val:
                        label = val
                        break

            if not label:
                label = type_name.split(".")[-1]  # fallback to type name

            for i, token in enumerate(doc):
                if token.idx >= begin and (token.idx + len(token)) <= end:
                    labels[i] = f"B-{label}" if token.idx == begin else f"I-{label}"

    return tokens, labels

def convert_location_labels(tokens, labels, city_list_path, region_list_path, country_list_path):
    """
    This function converts the location labels into city, country and region annotations
    Parameters:
        tokens : A list of tokens
        labels: A list of labels with locationNames tags
    Returns:
        labels: labels with the location tags replaced with city, country and region annotations
    """
    # Load the list of cities (lowercased for consistent comparison)
    with open(city_list_path, "r", encoding="utf-8") as f:
        city_list = set(city.lower() for city in json.load(f))

    with open(region_list_path, "r", encoding="utf-8") as f:
        region_list = set(region.lower() for region in json.load(f))

    with open(country_list_path, "r", encoding="utf-8") as f:
        country_list = set(country.lower() for country in json.load(f))
    i = 0
    while i < len(labels):
        label = labels[i]

        if label == "B-locationName" or label == "B-Location":
            entity_tokens = [i]
            j = i + 1
            if label == "B-locationName":
                while j < len(labels) and labels[j] == "I-locationName":
                    entity_tokens.append(j)
                    j += 1
                entity_text = " ".join(tokens[k] for k in entity_tokens)
            else:
                while j < len(labels) and labels[j] == "I-Location":
                    entity_tokens.append(j)
                    j += 1
                entity_text = " ".join(tokens[k] for k in entity_tokens)
            # Check if entity is a known city
            if entity_text.lower() in city_list:
                labels[i] = "B-city"
                for k in entity_tokens[1:]:
                    labels[k] = "I-city"
            elif entity_text.lower() in region_list:
                labels[i] = "B-region"
                for k in entity_tokens[1:]:
                    labels[k] = "I-region"
            elif entity_text.lower() in country_list:
                labels[i] = "B-country"
                for k in entity_tokens[1:]:
                    labels[k] = "I-country"
            else:
                # If not found in any list, keep as locationName
                labels[i] = "O"
                for k in entity_tokens[1:]:
                    labels[k] = "O"
            i = j
        else:
            i += 1
    return labels

def remove_labels(labels: list, remove_labels: list):
    """
    This function takes a list of labels and removes some defined labels from it
    Parameters:
    - labels: The list of labels to be modified
    - remove_labels: A list of labels that should be removed from the list
    Returns:
    - A new list with the specified labels removed
    """
    return [label if label not in remove_labels else "O" for label in labels]

def cas_to_hf_entities(
    cas,
    annotation_types = [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ],
):
    """
    Convert a CAS document into:
      - the raw text (cas.sofa_string)
      - a list of entities in HuggingFace NER 'simple' aggregation format

    Each entity is a dict:
        {
            "entity_group": <label>,
            "word": <surface form>,
            "start": <char_start>,
            "end": <char_end>
        }

    Parameters
    ----------
    cas : CAS
        The CAS object representing the document.
    annotation_types : list of str
        Fully-qualified UIMA type names for the annotations to convert.

    Returns
    -------
    text : str
        The full document text.
    entities : list of dict
        List of entity dicts in HF format.
    """
    text = cas.sofa_string
    entities = []

    for type_name in annotation_types:
        for ann in cas.select(type_name):
            begin = ann.begin
            end = ann.end

            # Determine the label, same logic as in cas_to_bio
            label = None
            for feat in ann.type.all_features:
                if feat.name in ("sofa", "begin", "end"):
                    continue
                if hasattr(ann, feat.name):
                    val = getattr(ann, feat.name)
                    if val:
                        label = val
                        break

            # Fallback to type name if no feature value is set
            if not label:
                label = type_name.split(".")[-1]

            surface = text[begin:end]

            entities.append({
                "entity_group": label,
                "word": surface,
                "start": begin,
                "end": end
            })

    # Sort by character position to keep entities in text order
    entities.sort(key=lambda e: (e["start"], e["end"]))

    return text, entities


def cas_to_hf_entities_json(
    cas,
    annotation_types = [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ],
):
    """
    Convenience wrapper: same as cas_to_hf_entities,
    but returns the entities as a JSON string.
    """
    text, entities = cas_to_hf_entities(cas, annotation_types)
    entities_json = json.dumps(entities, ensure_ascii=False)
    return text, entities_json