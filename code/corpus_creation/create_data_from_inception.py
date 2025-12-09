import pandas as pd
import argparse
from cas_to_csv_sentence import generate_csv_from_cas_curation, generate_csv_from_cas
from cas_to_csv_files import (generate_csv_from_cas_curation_files, generate_csv_from_cas_files,
                              generate_text_labels_from_cas_files_curation, generate_text_labels_from_cas_files)
from internal_id_to_doi import load_dataset_dict, map_doi

if __name__ == "__main__":
    # create a dataframe to store all the data
    # Define the column types
    parser = argparse.ArgumentParser(description="FAIRagro entity distribution plotting")

    parser.add_argument(
        "--parent_folder",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/webanno17101708295286074066export_curated_documents/curation",
        help="Path to the parent folder with curated documents"
    )
    parser.add_argument(
        "--parent_folder_leo",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/admin-58560539323484181674/annotation",
        help="Path to the Leo parent folder"
    )
    parser.add_argument(
        "--city_list_path",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/de_cities_list.json",
        help="Path to the cities list JSON file"
    )
    parser.add_argument(
        "--region_list_path",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/de_regions_list.json",
        help="Path to the regions list JSON file"
    )
    parser.add_argument(
        "--country_list_path",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/countries_list.json",
        help="Path to the countries list JSON file"
    )
    parser.add_argument(
        "--save_csv",
        type=str,
        default="sentences_corpus.csv",
        help="Filename to save the processed sentences corpus as CSV"
    )
    parser.add_argument(
        "--bonares_middleware",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/bonares_middleware.json",
        help="Path to the middleware data of BonaRes"
    )
    parser.add_argument(
        "--openagrar_middleware",
        type=str,
        default="/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/openagrar.json",
        help="Path to the middleware data of OpenAgrar"
    )

    args = parser.parse_args()
    # Create actual variables
    parent_folder = args.parent_folder
    parent_folder_leo = args.parent_folder_leo
    city_list_path = args.city_list_path
    region_list_path = args.region_list_path
    country_list_path = args.country_list_path
    save_csv = args.save_csv
    bonares_dict_path = args.bonares_middleware
    openagrar_dict_path = args.openagrar_middleware
    # Load the metadata only once
    bonares_dict = load_dataset_dict(bonares_dict_path)
    openagrar_dict = load_dataset_dict(openagrar_dict_path)
    # create the corpus dataframe
    columns = {
        "file_name": pd.StringDtype(),
        "Tokens": object,            # list of strings
        "ner_tags": object,
        "Labels": object,            # list of strings
        "number_of_tokens": int,
        "Language": pd.StringDtype(),
        "source": pd.StringDtype(),
        "Label_counts": object,      # Counter object (from collections)
        "number_of_annotations": int,# sum of values in Label_counts
        "doi": pd.StringDtype()
    }
    columns_json_format = {
        "file_name": pd.StringDtype(),
        "text": pd.StringDtype(),  # list of strings
        "entities": object,  # list of strings
        "Language": pd.StringDtype(),
        "source": pd.StringDtype(),
        "Label_counts": object,  # Counter object (from collections)
        "number_of_annotations": int,# sum of values in Label_counts
        "doi": pd.StringDtype()
    }

    # Create the empty DataFrame for sentences
    df_sentences = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in columns.items()})
    # Fetch thed data from the curated project
    df_sentences = generate_csv_from_cas_curation(df_sentences, parent_folder, city_list_path, region_list_path, country_list_path)
    # Fetch the data from the annoation project
    df_sentences = generate_csv_from_cas(df_sentences, parent_folder_leo, "GolzL.zip", city_list_path, region_list_path, country_list_path)
    #add the doi information
    df_sentences["doi"] = df_sentences.apply(
        lambda row: map_doi(row, bonares_dict, openagrar_dict),
        axis=1,
    )
    # # create the empty dataframe for file datasets
    # df_files = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in columns.items()})
    # # Fetch thed data from the curated project
    # df_files = generate_csv_from_cas_curation_files(df_files, parent_folder, city_list_path, region_list_path, country_list_path)
    # # Fetch the data from the annoation project
    # df_files = generate_csv_from_cas_files(df_files, parent_folder_leo, "GolzL.zip", city_list_path, region_list_path, country_list_path)
    # # add the doi information
    # df_files["doi"] = df_files.apply(
    #     lambda row: map_doi(row, bonares_dict, openagrar_dict),
    #     axis=1,
    # )
    # Split data into test and training datasets
    # create the empty dataframe for file datasets
    # df_files_json = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in columns_json_format.items()})
    # # Fetch thed data from the curated project
    # df_files_json = generate_text_labels_from_cas_files_curation(df_files_json, parent_folder, city_list_path, region_list_path, country_list_path)
    # # Fetch the data from the annoation project
    # df_files_json = generate_text_labels_from_cas_files(df_files_json, parent_folder_leo, "GolzL.zip", city_list_path, region_list_path, country_list_path)
    # # add the doi information
    # df_files_json["doi"] = df_files_json.apply(
    #     lambda row: map_doi(row, bonares_dict, openagrar_dict),
    #     axis=1,
    # )
    # Test set file names
    test_set = ['49873.txt', 
                '73465.txt', 
                '102130.txt', 
                '100184.txt', 
                '36710.txt', 
                '101198.txt', 
                '41381.txt', 
                '67631.txt', 
                '41963.txt', 
                '41808.txt', 
                '102268.txt', 
                '102239.txt', 
                '102137.txt', 
                '36149.txt', 
                '74475.txt', 
                '92044.txt', 
                '87621.txt', 
                '101017.txt', 
                '101378.txt', 
                '50596.txt', 
                '62744.txt', 
                '48159.txt', 
                '97378.txt', 
                '286a674c-1bcd-4a35-b78f-7e980a89d6fa.txt', 
                '0007bad6-848d-4763-9813-d5ed21cde6ee.txt', 
                '98833.txt', 
                'b963432a-9114-4cc0-8387-536c333bc123.txt', 
                '8170ee67-01c9-42b6-82ae-1b6442e5bdc3.txt', 
                '97dda154-93d3-4685-beff-9124e7346d68.txt', 
                '9b296f99-f6a0-423c-9716-6a04fd2e502f.txt', 
                '95868.txt']  
    # split the data into train and test datasets
    test_df = df_sentences[df_sentences["file_name"].isin(test_set)]
    train_df = df_sentences[~df_sentences["file_name"].isin(test_set)]
    # test_df_files = df_files[df_files["file_name"].isin(test_set)]
    # train_df_files = df_files[~df_files["file_name"].isin(test_set)]
    # test_df_files_json = df_files_json[df_files_json["file_name"].isin(test_set)]
    # train_df_files_json = df_files_json[~df_files_json["file_name"].isin(test_set)]
    # save the csv files accordingly
    train_df.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/train_sentence_corpus.csv", index=False)
    test_df.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/test_sentence_corpus.csv", index=False)

    # save the csv files accordingly
    # train_df_files.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/train_files_corpus.csv", index=False)
    # test_df_files.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/test_files_corpus.csv", index=False)

    # # save the csv files accordingly
    # test_df_files_json.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/train_files_json_corpus.csv", index=False)
    # train_df_files_json.to_csv("/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/code/corpus_creation/dataset_files/test_files_json_corpus.csv", index=False)