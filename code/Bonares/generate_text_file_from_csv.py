import csv
import os

def csv_rows_to_selected_text_files(csv_file_path, output_folder, selected_columns):
    """
    Creates a separate text file for each row in the CSV file, writing only specified columns.

    Parameters:
    - csv_file_path: Path to the input CSV file.
    - output_folder: Path to the folder where the text files will be saved.
    - selected_columns: A list of column names to include in the text files.
    """
    try:
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)  # Use DictReader for column name mapping

            for i, row in enumerate(reader):
                # Create a unique filename for each row
                text_file_path = os.path.join(output_folder, f'{row['ID']}.txt')

                # Write only selected columns to the text file
                with open(text_file_path, 'w', encoding='utf-8') as text_file:
                    for col_name in selected_columns:
                        if col_name in row:
                            text_file.write(f"{col_name.capitalize()}: \n {row[col_name]}\n")

        print(f"Text files created successfully in {output_folder}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
csv_file_path = '/Users/husain/pilot-uc-textmining-metadata/data/Bonares/output/output_new_data.csv'  # Replace with your CSV file path
output_folder = '/Users/husain/pilot-uc-textmining-metadata/data/Bonares/output/output_text_files'  # Replace with your desired folder path
selected_columns = ['title', 'abstract_text_1', 'abstract_text_2', 'keywords']  # Specify the columns you want to include
csv_rows_to_selected_text_files(csv_file_path, output_folder, selected_columns)
