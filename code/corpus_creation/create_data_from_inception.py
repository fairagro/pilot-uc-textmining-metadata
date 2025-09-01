import pandas as pd
import argparse
from cas_to_csv_sentence import generate_csv_from_cas_curation, generate_csv_from_cas
from cas_to_csv_files import generate_csv_from_cas_curation_files, generate_csv_from_cas_files


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

    args = parser.parse_args()
    # Create actual variables
    parent_folder = args.parent_folder
    parent_folder_leo = args.parent_folder_leo
    city_list_path = args.city_list_path
    region_list_path = args.region_list_path
    country_list_path = args.country_list_path
    save_csv = args.save_csv
    # create the corpus dataframe
    columns = {
        "file_name": pd.StringDtype(),
        "Tokens": object,            # list of strings
        "Labels": object,            # list of strings
        "number_of_tokens": int,
        "Language": pd.StringDtype(),
        "source": pd.StringDtype(),
        "Label_counts": object,      # Counter object (from collections)
        "number_of_annotations": int     # sum of values in Label_counts
    }

    # Create the empty DataFrame for sentences
    df_sentences = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in columns.items()})
    # Fetch thed data from the curated project
    df_sentences = generate_csv_from_cas_curation(df_sentences, parent_folder, city_list_path, region_list_path, country_list_path)
    # Fetch the data from the annoation project
    df_sentences = generate_csv_from_cas(df_sentences, parent_folder_leo, "GolzL.zip", city_list_path, region_list_path, country_list_path)
    
    # create the empty dataframe for file datasets
    df_files = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in columns.items()})
    # Fetch thed data from the curated project
    df_files = generate_csv_from_cas_curation_files(df_files, parent_folder, city_list_path, region_list_path, country_list_path)
    # Fetch the data from the annoation project
    df_files = generate_csv_from_cas_files(df_files, parent_folder_leo, "GolzL.zip", city_list_path, region_list_path, country_list_path)
    # Split data into test and training datasets
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
    test_df_files = df_files[df_files["file_name"].isin(test_set)]
    train_df_files = df_files[~df_files["file_name"].isin(test_set)]
    # save the csv files accordingly
    train_df.to_csv("/output/train_sentence_corpus.csv", index=False)
    test_df.to_csv("/output/test_sentence_corpus.csv", index=False)

    # save the csv files accordingly
    train_df_files.to_csv("/output/train_files_corpus.csv", index=False)
    test_df_files.to_csv("/output/test_files_corpus.csv", index=False)