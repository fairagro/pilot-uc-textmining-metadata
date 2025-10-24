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
from cas_to_tokens import cas_sentence_to_bio, convert_location_labels
from cas_folders_processing import process_inception_folder, process_parent_folder_curation
nlp = spacy.load("en_core_web_sm")
label_list = ["O","B-soilReferenceGroup","I-soilReferenceGroup", "B-soilOrganicCarbon", "I-soilOrganicCarbon", "B-soilTexture", "I-soilTexture",
               "B-startTime", "I-startTime", "B-endTime", "I-endTime", "B-city", "I-city", "B-duration", "I-duration", "B-cropSpecies", "I-cropSpecies",
                 "B-soilAvailableNitrogen", "I-soilAvailableNitrogen", "B-soilDepth", "I-soilDepth", "B-region", "I-region", "B-country", "I-country",
                   "B-longitude", "I-longitude", "B-latitude", "I-latitude", "B-cropVariety", "I-cropVariety", "B-soilPH", "I-soilPH",
                     "B-soilBulkDensity", "I-soilBulkDensity", 'B-Timestatement', 'I-Timestatement']
label_to_index = {label: idx for idx, label in enumerate(label_list)}
def safe_detect(text):
    try:
        if not text or text.strip() == "":
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"

def generate_csv_from_cas(df, cas_path, target_zip, city_list_path, region_list_path, country_list_path):
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
            for i, sentence in enumerate(cas.select("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")):
                sentence_id = f"{file_name[:-4]}-{i}"  # e.g., 93535-0
                sentence_text = text[sentence.begin:sentence.end]
                
                tokens, labels = cas_sentence_to_bio(cas, sentence)
                labels = convert_location_labels(tokens, labels, city_list_path, region_list_path, country_list_path)
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
                    "Language": safe_detect(str(sentence_text)),                 # or any other source if you have
                    "source": source,                  # optional source info
                    "Label_counts": label_counts,
                    "number_of_annotations": number_of_annotations,
                    "sentence_id": sentence_id
                }])], ignore_index=True)
    return df



def generate_csv_from_cas_curation(df, cas_path, city_list_path, region_list_path, country_list_path):
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
            for i, sentence in enumerate(cas.select("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")):
                sentence_id = f"{file_name[:-4]}-{i}"  # e.g., 93535-0
                sentence_text = text[sentence.begin:sentence.end]
                
                tokens, labels = cas_sentence_to_bio(cas, sentence)
                original = labels
                labels = convert_location_labels(tokens, labels, city_list_path, region_list_path, country_list_path)
                # Filter labels to exclude "O" and labels starting with "I-"
                filtered_labels = [lbl[2:] for lbl in labels if lbl != "O" and not lbl.startswith("I-")]
                # Count filtered labels
                label_counts = Counter(filtered_labels)
                number_of_annotations = sum(label_counts.values())
                if len(file_name)>9:
                    source = "BonaRes"
                else:
                    source = "OpenAgrar"
                # Append row to DataFrame
                ner_tags = []
                for label in labels:
                    try:
                        ner_tags.append(label_to_index[label])
                    except KeyError:
                        ner_tags.append(0)
                df = pd.concat([df, pd.DataFrame([{
                    "file_name": file_name,
                    "Tokens": tokens,
                    "ner_tags": ner_tags,
                    "Labels": labels,
                    "number_of_tokens": len(tokens),
                    "Language": safe_detect(str(sentence_text)),                 # or any other source if you have
                    "source": source,                  # optional source info
                    "Label_counts": label_counts,
                    "number_of_annotations": number_of_annotations,
                    "sentence_id": sentence_id
                }])], ignore_index=True)
    return df
        
        