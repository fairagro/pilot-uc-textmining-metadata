import os
import spacy
from spacy.pipeline import EntityRuler

# Load spaCy model
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# Define custom annotation rules
patterns = [
    {"label": "COMPANY", "pattern": "Tesla"},
    {"label": "CEO", "pattern": "Elon Musk"},
]

ruler.add_patterns(patterns)

def annotate_text_file(input_file_path, output_file_path):
    """Reads a text file, processes it with spaCy, and writes annotations to a new file."""
    with open(input_file_path, "r", encoding="utf-8") as file:
        text = file.read()
    
    # Process text
    doc = nlp(text)
    
    # Generate annotated text
    annotated_text = text
    for ent in reversed(doc.ents):  # Reverse to avoid shifting positions
        annotated_text = (annotated_text[:ent.start_char] + 
                          f"[{ent.text}]({ent.label_})" + 
                          annotated_text[ent.end_char:])
    
    # Write to the new file
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(annotated_text)

def process_directory(input_directory, output_directory):
    """Processes all text files in a directory and saves the annotated files to a new directory."""
    os.makedirs(output_directory, exist_ok=True)
    
    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):  # Process only text files
            input_file_path = os.path.join(input_directory, filename)
            output_file_path = os.path.join(output_directory, filename)
            annotate_text_file(input_file_path, output_file_path)
            print(f"Annotated {filename} and saved to {output_directory}")

# Example usage
input_directory = "/home/s27mhusa_hpc/pilot-uc-textmining-metadata/data/Bonares/output/TextFiles_filtered_df_soil_crop_year"  # Replace with your actual input directory path
output_directory = "/home/s27mhusa_hpc/pilot-uc-textmining-metadata/data/Bonares/output/TextFiles_filtered_df_soil_crop_year_annotated"  # Directory to save annotated files
process_directory(input_directory, output_directory)
