import sys
from collections import Counter
import json
from langdetect import detect
import pandas as pd
from collections import Counter
from viz_funcs import data_statistics_extend, plot_entity_distribution_by, plot_entity_distribution_list, add_numerical_ner_tags
from cassis import *
import spacy
import os
import zipfile

def process_parent_folder_curation(parent_folder):
    """
    Loops over all .xmi folders in parent_folder,
    finds the zip file inside each,
    and collects:
        - xmi files inside the zip
        - TypeSystem.xml files inside the zip
        - derived .txt file name (based on folder name)
    Parameters:
        inception_folder (str): path to the folder containing all the documents
    Returns:
        - all_xmi_files: A list of pathes to all the xmi files for each document
        - all_typesystem_files: A list of all pathes to typesystem files
        - all_txt_files: All files names that are their ID's 

    """
    all_xmi_files = []
    all_typesystem_files = []
    all_txt_files = []

    for folder_name in os.listdir(parent_folder):
        folder_path = os.path.join(parent_folder, folder_name)
        if os.path.isdir(folder_path) and folder_name.endswith(".xmi"):
            # Look for any zip in this folder
            zip_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".zip")]
            if not zip_files:
                print(f"No zip files found in {folder_path}, skipping")
                continue
            zip_path = os.path.join(folder_path, zip_files[0])
            target_xmi = zip_files[0].split(".")[0] + ".xmi"

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for f in zip_ref.namelist():
                    if f.endswith("CURATION_USER.xmi"):
                        all_xmi_files.append(os.path.join(zip_path, f))
                    elif f.endswith("TypeSystem.xml"):
                        all_typesystem_files.append(os.path.join(zip_path, f))
                        # Extract numeric ID from folder name
                        base_id = folder_name.split("_")[0]
                        all_txt_files.append(base_id + ".txt")

    return all_xmi_files, all_typesystem_files, all_txt_files

def process_inception_folder(inception_folder, target_zip="GolzL.zip"):
    """
    Takes a folder like '/path/.../93535_inception.xmi'
    Looks inside its GolzL.zip
    Returns three lists:
      - target_xmi files (inside the zip)
      - TypeSystem.xml files (inside the zip)
      - One derived txt file name (93535.txt)
    
    Parameters:
        inception_folder (str): path to the folder containing GolzL.zip
        target_zip (str): name of the zip file to look for (default "GolzL.zip")
    Returns:
        - all_xmi_files: A list of pathes to all the xmi files for each document
        - all_typesystem_files: A list of all pathes to typesystem files
        - all_txt_files: All files names that are their ID's 
    """
    golz_xmi_files = []
    typesystem_files = []
    txt_files = []  # new list for 93535.txt style names
    target_xmi = target_zip.split(".")[0]+".xmi"
    for root, dirs, files in os.walk(inception_folder):
        if target_zip in files:
            zip_path = os.path.join(root, target_zip)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for f in zip_ref.namelist():
                    if f.endswith(target_xmi):
                        golz_xmi_files.append(os.path.join(zip_path, f))
                    elif f.endswith("TypeSystem.xml"):
                        typesystem_files.append(os.path.join(zip_path, f))
                        
                        # Extract the numeric ID before "_inception.xmi"
                        parts = root.split(os.sep)  # split path into folders
                        for p in parts:
                            if p.endswith("_inception.xmi"):
                                base_id = p.split("_")[0]  
                                txt_files.append(base_id + ".txt")

    return golz_xmi_files, typesystem_files, txt_files

