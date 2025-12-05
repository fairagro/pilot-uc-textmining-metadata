'''
This file contains functions required to generate text files from saved abstracts and titles of Openagrar

'''
import ast
import argparse
import os
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
def keywords_from_agrovoc():


    # Define the SPARQL endpoint
    sparql_endpoint = "https://agrovoc.fao.org/sparql"

    # Define the SPARQL query
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
    SELECT DISTINCT ?hierarchicalType ?otherConcept ?label
    WHERE { 
      {
        BIND(<http://aims.fao.org/aos/agrovoc/c_1972> AS ?concept)
        ?concept skos:narrower ?otherConcept .
        BIND("narrower" AS ?hierarchicalType)
      }
      UNION
      {
        BIND(<http://aims.fao.org/aos/agrovoc/c_7156> AS ?concept)
        ?concept skos:narrower ?otherConcept .
        BIND("narrower" AS ?hierarchicalType)
      }
      UNION
      {
        BIND(<http://aims.fao.org/aos/agrovoc/c_5993> AS ?concept)
        ?concept skos:narrower ?otherConcept .
        BIND("narrower" AS ?hierarchicalType)
      }
      UNION
      {
        BIND(<http://aims.fao.org/aos/agrovoc/c_8171> AS ?concept)
        ?concept skos:narrower ?otherConcept .
        BIND("narrower" AS ?hierarchicalType)

      }
      OPTIONAL { 
        ?otherConcept skosxl:prefLabel/skosxl:literalForm ?label.
      }
      FILTER(langMatches(lang(?label), 'en')) 
    }
    """

    # Set up the SPARQL wrapper
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    soil_crop_list = []
    # Execute the query and fetch the results
    try:
        results = sparql.query().convert()
        print("Query executed successfully.")

        # Print results in a readable format
        for result in results["results"]["bindings"]:
            hierarchical_type = result.get("hierarchicalType", {}).get("value", "")
            other_concept = result.get("otherConcept", {}).get("value", "")
            label = result.get("label", {}).get("value", "")
            soil_crop_list.append(label)


    except Exception as e:
        print(f"An error occurred: {e}")
    return soil_crop_list
def csv_to_textfiles(csv_file_directory, text_files_directory):
    '''

    :param csv_file_directory: The directory where the csv file containing all the cleaned data is stored
    :param text_files_directory: The parent diretory where all the text files should be stored
    :return:
    '''
    openagrar = pd.read_csv(csv_file_directory, sep="|")
    # Ensure the dataset_files directory exists
    os.makedirs(text_files_directory, exist_ok=True)
    soil_crop_list = keywords_from_agrovoc()
    # Iterate over each row in the DataFrame
    for _, row in openagrar.iterrows():
        # Extract the `id`, `title`, and `abstract_text` for the current row
        file_id = row['ID']
        title = row['title']
        abstract_text = row['abstract_text'][1:-1]
        subjects = row['subjects']
        if str(subjects)[0] == '[':
            # print(subjects)
            subjects = ast.literal_eval(subjects.lower())
            for subject in subjects:
                if str(subject) in str(soil_crop_list) or 'soil' in str(subject) or 'crop' in str(subject):

                    # Create the content for the text file
                    content = f"Title: \n{title}\n\nAbstract:\n{abstract_text}"

                    # Define the file name and full path
                    file_name = f"{file_id}.txt"
                    file_path = os.path.join(text_files_directory, file_name)

                    # Write the content to a text file
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(content)

    print(f"Text files created successfully in directory: {text_files_directory}")

def main():
    """Main function to handle terminal input and call the file generation function."""
    parser = argparse.ArgumentParser(description="Generate text files from a CSV file.")
    parser.add_argument("--csv_file", type=str, required=True, help="Path to the input CSV file.")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory where the text files will be saved.")

    args = parser.parse_args()

    # Call the function to generate files
    csv_to_textfiles(args.csv_file, args.out_dir)

if __name__ == "__main__":
    main()