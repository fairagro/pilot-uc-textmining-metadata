import os
import sys
import spacy
from collections import Counter
import json
from langdetect import detect
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

def check_abctract_1(tokens, labels):
    """
    This function checks if the abstract and the title are duplicated and deletes the abstract 
    Parameters:
        tokens (list): A list of tokens from the file.
        labels (list): A list of labels corresponding to each token in the file.
    Returns:
        tokens: Updated tokens
        labels: Updated labels that align with the new tokens
    """
    
    title_tokens=[]
    abstract_1_tokens=[]
    abstract_found = False
    abstract_ended = False
    abstract_start = 0
    abstract_end = 1
    for index, token in enumerate(tokens):
        if token == "Abstract_text_1":
            abstract_start = index
            abstract_found = True
        if abstract_found == False:
            title_tokens.append(token)
        elif token == "Abstract_text_2":
            abstract_end = index
            abstract_ended = True
        elif abstract_ended == False:
            abstract_1_tokens.append(token)
        else:
            break
    if title_tokens[2:-1] == abstract_1_tokens[2:-3]:
        print("abstract_1 is same as title")
        del tokens[abstract_start:abstract_end]
        del labels[abstract_start:abstract_end]
    return tokens, labels
        
def data_statistics_extend(df, input_label_dir, input_token_dir):
    """
    This function extends a pandas dataframe with the labels and tokens in the input directories 
    Parameters:
        df : pandas.DataFrame
            A DataFrame for the statistics of the UC project with the format:
                {
                    "file_name": pd.StringDtype(),       # name of the file
                    "Tokens": object,                    # list of strings (tokenized text)
                    "Labels": object,                    # list of strings (labels per token)
                    "number_of_tokens": int,              # total number of tokens
                    "Language": pd.StringDtype(),        # language code or name
                    "source": pd.StringDtype(),          # origin/source of the data
                    "Label_counts": object,              # Counter object of label frequencies
                    "number_of_annotations": int         # sum of all label counts
                } 
        input_label_dir (str): Directory where the files containing the files that contain each of the labels
        input_token_dir (str): Directory that contains all the files that contain lists of the tokens
    Returns:
        df: Updated dataframe with the files form the directories 
    """
    for filename in os.listdir(input_label_dir):
        if not(filename[-2:] == 'er'):
            label_path = os.path.join(input_label_dir, filename)
            with open(label_path, "r", encoding="utf-8") as file:
                content = file.read()
            labels = eval(content)
            token_path = os.path.join(input_token_dir, f"tokens_{filename}")
            with open(token_path, "r", encoding="utf-8") as file:
                token_content = file.read()
            tokens = eval(token_content)
            text = " ".join(tokens)
            if detect(text) == "de":
                language = "de"
            else:
                language = "en"
            if len(filename) > 11:
                tokens, labels = check_abctract_1(tokens, labels)
                # Add the row
                new_row = {
                    "file_name": filename,
                    "Tokens": tokens,
                    "Labels": labels,
                    "number_of_tokens": len(tokens),
                    "Language": language,
                    "source": "BonaRes",
                    "Label_counts":  Counter(label[2:] for label in labels if label.startswith("B-")),
                    "number_of_annotations": sum(Counter(label[2:] for label in labels if label.startswith("B-")).values())
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                # Add the row
                new_row = {
                    "file_name": filename,
                    "Tokens": tokens,
                    "Labels": labels,
                    "number_of_tokens": len(tokens),
                    "Language": language,
                    "source": "OpenAgrar",
                    "Label_counts":  Counter(label[2:] for label in labels if label.startswith("B-")),
                    "number_of_annotations": sum(Counter(label[2:] for label in labels if label.startswith("B-")).values())
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
    print("new data added")
    return df

def plot_entity_distribution_by(df, column=None):
    """
    Plots separate bar charts for each language showing the count of each entity type,
    with custom styling and count labels above bars.

    Parameters:
        df (pd.DataFrame): Your annotated dataset
        column (str): The column you want to group the data by
    """
    if column == None:
        lang_df = df
        plot_df(lang_df)
    else:
        languages = df[column].unique()

        for lang in languages:
            # Filter the dataframe for the current language
            lang_df = df[df[column] == lang]
            plot_df(lang_df, f'Entity Label Counts - {lang}')

def plot_entity_distribution_list(df, column="file_name", files=[]):
    """
    Plots bar chart for the files in the list

    Parameters:
        df (pd.DataFrame): Your annotated dataset
        column (str): The column you want to group the data by
        files (list): contains the names of the files to be included
    """
    # Filter the DataFrame
    filtered_df = df[df[column].isin(files)]
    plot_df(filtered_df)

def plot_df(df, title = "Combined labels count"):
    # Filter the dataframe for the current language
    lang_df = df
    
    # Aggregate all Label_counts counters
    aggregated_counts = sum(lang_df["Label_counts"], Counter())

    # Prepare data for plotting
    labels = list(aggregated_counts.keys())
    counts = list(aggregated_counts.values())

    # Create bar chart
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, counts, color='lightseagreen')
    plt.title(title)
    plt.xlabel("Labels")
    plt.ylabel("Counts")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=90)
    final_group = {"Time":0,"Location":0,"Crop":0, "Soil":0}
    outer_to_inner = {
    "Time": ["startTime", "endTime", "duration"],
    "Crop": ["cropVariety", "cropSpecies"],
    "Location": ["country", "city", "region", "longitude", "latitude"],
    "Soil": [
        "soilDepth",
        "soilAvailableNitrogen",
        "soilOrganicCarbon",
        "soilPH",
        "soilBulkDensity",
        "soilTexture",
        "soilReferenceGroup"
    ]
}
    for key, value in aggregated_counts.items():
        if key in outer_to_inner["Time"]:
            final_group["Time"]+=value
        elif key in outer_to_inner["Crop"]:
            final_group["Crop"]+=value
        elif key in outer_to_inner["Location"]:
            final_group["Location"]+=value
        elif key in outer_to_inner["Soil"]:
            final_group["Soil"]+=value
    # Add count labels above bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 1,
            int(yval),
            ha='center',
            va='bottom'
        )
    print(f'number if files = {len(lang_df)}')
    print(aggregated_counts)
    print(sum(aggregated_counts.values()))
    print(final_group)
    plt.tight_layout()
    plt.show()

def add_numerical_ner_tags(df, labels_dict):
    """
    This function adds a column to the dataset that contains the ner tags similar to huggingface format
    Parameters:
        df (pd.DataFrame): Your annotated dataset
        labels_dict (dict): A dictionary containing the labels and their corresponding value in this format {"label": int} 
    Outputs:
        df: the same dataframe with the ner_tags added there
    """
    label2id = labels_dict

    # create the ner_tags column values
    ner_tags = df["Labels"].apply(lambda labels: [int(label2id[label]) for label in labels])

    # insert right after "Labels"
    labels_index = df.columns.get_loc("Labels")
    df.insert(labels_index + 1, "ner_tags", ner_tags)

    return df