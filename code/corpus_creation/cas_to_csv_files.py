"""
This file contains the code to convert the cas projects from Inception into csv files containing the corpus
"""

from collections import Counter
from langdetect import detect, LangDetectException
import pandas as pd
from collections import Counter
from cassis import *
import spacy
import zipfile
from cas_to_tokens import cas_files_to_bio, convert_location_labels, remove_labels, cas_to_hf_entities
from cas_folders_processing import process_inception_folder, process_parent_folder_curation

import json
nlp = spacy.load("en_core_web_sm")

label_list = ["O","B-soilReferenceGroup","I-soilReferenceGroup", "B-soilOrganicCarbon", "I-soilOrganicCarbon", "B-soilTexture", "I-soilTexture",
               "B-startTime", "I-startTime", "B-endTime", "I-endTime", "B-city", "I-city", "B-duration", "I-duration", "B-cropSpecies", "I-cropSpecies",
                 "B-soilAvailableNitrogen", "I-soilAvailableNitrogen", "B-soilDepth", "I-soilDepth", "B-region", "I-region", "B-country", "I-country",
                   "B-longitude", "I-longitude", "B-latitude", "I-latitude", "B-cropVariety", "I-cropVariety", "B-soilPH", "I-soilPH",
                     "B-soilBulkDensity", "I-soilBulkDensity"]
#labels_to_remove = ["B-soilDepth", "I-soilDepth", "B-soilPH", "I-soilPH"]
labels_to_remove = []
label_to_index = {label: idx for idx, label in enumerate(label_list)}

def safe_detect(text):
    try:
        if not text or text.strip() == "":
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"

def generate_csv_from_cas_files(df, cas_path, target_zip, city_list_path, region_list_path, country_list_path):
    """
    This function takes the directory to where all the xmi folders for each document are and the annotator we want to extract
    Then it generates the corpus as a dataframe that could be saved afterwards as a csv file or extended by more data
    Parameters:
        - df: The dataframe that should be extended (could be an empty dataframe with the correct columns)
        columns_names = {
                "sentence_id": pd.StringDtype(),
                "file_name": pd.StringDtype(),
                "Tokens": object,                  # list of strings
                "ner_tags": object                  #list of integers
                "Labels": object,                  # list of strings
                "number_of_tokens": int,
                "Language": pd.StringDtype(),
                "source": pd.StringDtype(),
                "Label_counts": object,            # Counter object (from collections)
                "number_of_annotations": int,      # sum of values in Label_counts
            }
        - cas_path: the path to the xmi folders
        - target_zip: the user we are looking to extract
    """
    golz_xmi, typesystem, txt_list = process_inception_folder(cas_path, target_zip="GolzL.zip")
    for file_name, type_system_path, target in zip(txt_list, typesystem, golz_xmi):
        # Split the path into zip file and inner path
        zip_index = type_system_path.lower().rfind(".zip")  # find where .zip ends
        zip_path = type_system_path[:zip_index+4]          # include ".zip"
        type_system_innder_path = type_system_path[zip_index+5:]
        zip_index = target.lower().rfind(".zip")  # find where .zip ends
        zip_path = target[:zip_index+4]          # include ".zip"
        target_innder_path = target.split("zip")[1][1:]
        with zipfile.ZipFile(zip_path, "r") as z:
            with z.open(type_system_innder_path, 'r') as f:
                typesystem = load_typesystem(f)

            with z.open(target_innder_path, 'r') as f:
                cas = load_cas_from_xmi(f, typesystem=typesystem)
            text = cas.sofa_string
            
            tokens, labels = cas_files_to_bio(cas)
            labels = convert_location_labels(tokens, labels, city_list_path, region_list_path, country_list_path)
            # remove the low IAA labels
            labels = remove_labels(labels, labels_to_remove)
            # Filter labels to exclude "O" and labels starting with "I-"
            filtered_labels = [lbl[2:] for lbl in labels if lbl != "O" and not lbl.startswith("I-")]
             
            # Count filtered labels
            label_counts = Counter(filtered_labels)
            number_of_annotations = sum(label_counts.values())
            if len(file_name)>9:
                source = "BonaRes"
            else:
                source = "OpenAgrar"
            ner_tags = []
            for label in labels:
                try:
                    ner_tags.append(label_to_index[label])
                except KeyError:
                    ner_tags.append(0)
            # Append row to DataFrame
            df = pd.concat([df, pd.DataFrame([{
                "file_name": file_name,
                "Tokens": tokens,
                "ner_tags": ner_tags,
                "Labels": labels,
                "number_of_tokens": len(tokens),
                "Language": safe_detect(str(text)),                 # or any other source if you have
                "source": source,                  # optional source info
                "Label_counts": label_counts,
                "number_of_annotations": number_of_annotations
            }])], ignore_index=True)
    return df



def generate_csv_from_cas_curation_files(df, cas_path, city_list_path, region_list_path, country_list_path):
    """
    This function takes the directory to where all the xmi folders for each document are and the annotator we want to extract
    Then it generates the corpus as a dataframe that could be saved afterwards as a csv file or extended by more data
    Parameters:
        - df: The dataframe that should be extended (could be an empty dataframe with the correct columns)
        columns_names = {
                "sentence_id": pd.StringDtype(),
                "file_name": pd.StringDtype(),
                "Tokens": object,                  # list of strings
                "ner_tags": object                  #list of integers
                "Labels": object,                  # list of strings
                "number_of_tokens": int,
                "Language": pd.StringDtype(),
                "source": pd.StringDtype(),
                "Label_counts": object,            # Counter object (from collections)
                "number_of_annotations": int,      # sum of values in Label_counts
            }
        - cas_path: the path to the xmi folders
        - target_zip: the user we are looking to extract
    """
    golz_xmi, typesystem, txt_list = process_parent_folder_curation(cas_path)
    for file_name, type_system_path, target in zip(txt_list, typesystem, golz_xmi):
        # Split the path into zip file and inner path
        zip_index = type_system_path.lower().rfind(".zip")  # find where .zip ends
        zip_path = type_system_path[:zip_index+4]          # include ".zip"
        type_system_innder_path = type_system_path[zip_index+5:]
        zip_index = target.lower().rfind(".zip")  # find where .zip ends
        zip_path = target[:zip_index+4]          # include ".zip"
        target_innder_path = target.split("zip")[1][1:]
        with zipfile.ZipFile(zip_path, "r") as z:
            with z.open(type_system_innder_path, 'r') as f:
                typesystem = load_typesystem(f)

            with z.open(target_innder_path, 'r') as f:
                cas = load_cas_from_xmi(f, typesystem=typesystem)
            text = cas.sofa_string
            
            tokens, labels = cas_files_to_bio(cas)
            labels = convert_location_labels(tokens, labels, city_list_path, region_list_path, country_list_path)
            # remove the low IAA labels
            labels = remove_labels(labels, labels_to_remove)
            # Filter labels to exclude "O" and labels starting with "I-"
            filtered_labels = [lbl[2:] for lbl in labels if lbl != "O" and not lbl.startswith("I-")]
            # Count filtered labels
            label_counts = Counter(filtered_labels)
            
            number_of_annotations = sum(label_counts.values())
            if len(file_name)>9:
                source = "BonaRes"
            else:
                source = "OpenAgrar"
            ner_tags = []
            for label in labels:
                try:
                    ner_tags.append(label_to_index[label])
                except KeyError:
                    ner_tags.append(0)
            # Append row to DataFrame
            df = pd.concat([df, pd.DataFrame([{
                "file_name": file_name,
                "Text": tokens,
                "ner_tags": ner_tags,
                "Labels": labels,
                "number_of_tokens": len(tokens),
                "Language": safe_detect(str(text)),                 # or any other source if you have
                "source": source,                  # optional source info
                "Label_counts": label_counts,
                "number_of_annotations": number_of_annotations
            }])], ignore_index=True)
    return df
        
def generate_text_labels_from_cas_files(
    df,
    cas_path,
    target_zip,
    city_list_path,
    region_list_path,
    country_list_path,
    annotation_types = [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ],
):
    """
    Similar to generate_csv_from_cas_files, but produces a document-level
    DataFrame with:
      - file_name
      - text (full CAS sofa_string)
      - entities (JSON list of HF-style entity dicts)
      - Language
      - source
      - Label_counts
      - number_of_annotations
    """
    golz_xmi, typesystems, txt_list = process_inception_folder(cas_path, target_zip=target_zip)

    for file_name, type_system_path, target in zip(txt_list, typesystems, golz_xmi):
        # Split the path into zip file and inner path for typesystem
        zip_index = type_system_path.lower().rfind(".zip")
        zip_path = type_system_path[:zip_index + 4]          # include ".zip"
        type_system_inner_path = type_system_path[zip_index + 5:]

        # Split the path into zip file and inner path for CAS
        zip_index = target.lower().rfind(".zip")
        zip_path_cas = target[:zip_index + 4]                # include ".zip"
        target_inner_path = target.split("zip", 1)[1][1:]    # after "zip/"

        # Load CAS
        with zipfile.ZipFile(zip_path, "r") as z:
            with z.open(type_system_inner_path, "r") as f:
                typesystem = load_typesystem(f)

        with zipfile.ZipFile(zip_path_cas, "r") as z:
            with z.open(target_inner_path, "r") as f:
                cas = load_cas_from_xmi(f, typesystem=typesystem)

        # Get raw text + span entities from CAS
        text, entities = cas_to_hf_entities(cas, annotation_types=annotation_types)

        # Location refinement via gazetteers
        #entities = convert_location_entities(entities, city_list_path, region_list_path, country_list_path)

        # Optional: remove low-IAA labels if you use the same scheme
        try:
            entities = [e for e in entities if e["entity_group"] not in labels_to_remove]
        except NameError:
            # labels_to_remove not defined → skip this step
            pass

        # Compute counts
        filtered_labels = [e["entity_group"] for e in entities]
        label_counts = Counter(filtered_labels)
        number_of_annotations = sum(label_counts.values())

        # Source heuristic (same as your existing code)
        if len(file_name) > 9:
            source = "BonaRes"
        else:
            source = "OpenAgrar"

        # Append row to df
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "file_name": file_name,
                            "text": text,
                            # JSON list of entities as HF-style dicts
                            "entities": json.dumps(entities, ensure_ascii=False),
                            "Language": safe_detect(str(text)),
                            "source": source,
                            "Label_counts": label_counts,
                            "number_of_annotations": number_of_annotations,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return df

def generate_text_labels_from_cas_files_curation(
    df,
    cas_path,
    city_list_path,
    region_list_path,
    country_list_path,
    annotation_types = [
        "webanno.custom.Crops",
        "webanno.custom.Location",
        "webanno.custom.Soil",
        "webanno.custom.Timestatement",
    ],
):
    """
    Similar to generate_csv_from_cas_files, but produces a document-level
    DataFrame with:
      - file_name
      - text (full CAS sofa_string)
      - entities (JSON list of HF-style entity dicts)
      - Language
      - source
      - Label_counts
      - number_of_annotations
    """
    golz_xmi, typesystem, txt_list = process_parent_folder_curation(cas_path)
    for file_name, type_system_path, target in zip(txt_list, typesystem, golz_xmi):
        # Split the path into zip file and inner path
        zip_index = type_system_path.lower().rfind(".zip")  # find where .zip ends
        zip_path = type_system_path[:zip_index + 4]  # include ".zip"
        type_system_innder_path = type_system_path[zip_index + 5:]
        zip_index = target.lower().rfind(".zip")  # find where .zip ends
        zip_path = target[:zip_index + 4]  # include ".zip"
        target_innder_path = target.split("zip")[1][1:]
        with zipfile.ZipFile(zip_path, "r") as z:
            with z.open(type_system_innder_path, 'r') as f:
                typesystem = load_typesystem(f)

            with z.open(target_innder_path, 'r') as f:
                cas = load_cas_from_xmi(f, typesystem=typesystem)

        # Get raw text + span entities from CAS
        text, entities = cas_to_hf_entities(cas, annotation_types=annotation_types)

        # Location refinement via gazetteers
        #entities = convert_location_entities(entities, city_list_path, region_list_path, country_list_path)

        # Optional: remove low-IAA labels if you use the same scheme
        try:
            entities = [e for e in entities if e["entity_group"] not in labels_to_remove]
        except NameError:
            # labels_to_remove not defined → skip this step
            pass

        # Compute counts
        filtered_labels = [e["entity_group"] for e in entities]
        label_counts = Counter(filtered_labels)
        number_of_annotations = sum(label_counts.values())

        # Source heuristic (same as your existing code)
        if len(file_name) > 9:
            source = "BonaRes"
        else:
            source = "OpenAgrar"

        # Append row to df
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "file_name": file_name,
                            "text": text,
                            # JSON list of entities as HF-style dicts
                            "entities": json.dumps(entities, ensure_ascii=False),
                            "Language": safe_detect(str(text)),
                            "source": source,
                            "Label_counts": label_counts,
                            "number_of_annotations": number_of_annotations,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return df