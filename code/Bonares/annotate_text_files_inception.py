import spacy
import json
import os
from spacy.matcher import Matcher
from spacy import displacy
from cassis import *


def initialize_nlp_with_entity_ruler():
    model_name= "en_core_web_sm"
    species_file= r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\species_list.json"
    soilTexture_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\soilTexture_list.json" 
    bulkDensity_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\bulkDensity_list.json" 

    nlp = spacy.load(model_name)
    
    # Remove default NER so only custom entities are recognized
    nlp.disable_pipes("ner")

    # Load species list from JSON
    def load_concept_list(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    species_list = load_concept_list(species_file)
    soilTexture_list = load_concept_list(soilTexture_file)
    bulkDensity_list = load_concept_list(bulkDensity_file)

    # Define the matcher
    matcher = Matcher(nlp.vocab)

    # Define a pattern for soil depth recognition with multiple units
    depth_pattern_1 = [
    {"LIKE_NUM": True},  # Matches any number (e.g., 20, 35, 50)
    {"LOWER": ",", "OP": "?"},  # Optionally matches commas
    {"LOWER": "and", "OP": "?"},  # Optionally matches "and"
    {"LOWER": {"IN": ["mm", "cm", "m", "in"]}, "OP": "?"},  # Optionally matches units
    {"LOWER": "depth", "OP": "?"}  # Optionally matches "depth"
    ]

    depth_pattern_2 = [
        {"LOWER": "depth"},  # Matches "depth" appearing first
        {"LOWER": "of", "OP": "?"},  # Optionally matches "of" (e.g., "depth of 20 cm")
        {"LIKE_NUM": True},  # Matches any number
        {"LOWER": ",", "OP": "?"},  # Optionally matches commas
        {"LOWER": "and", "OP": "?"},  # Optionally matches "and"
        {"LOWER": {"IN": ["mm", "cm", "m", "in"]}, "OP": "?"}  # Optionally matches units
    ]

    # Add pattern to matcher
    matcher.add("soilDepth", [depth_pattern_1, depth_pattern_2])

    # Add EntityRuler with crop species patterns
    ruler = nlp.add_pipe("entity_ruler")
    patterns = (
    [{"label": "cropSpecies", "pattern": [{"LOWER": species.lower()}]} for species in species_list] +
    [{"label": "soilTexture", "pattern": [{"LOWER": soilTexture.lower()}]} for soilTexture in soilTexture_list] +
    [{"label": "soilBulkDensity", "pattern": [{"LOWER": bulkDensity.lower()}]} for bulkDensity in bulkDensity_list]
)


    ruler.add_patterns(patterns)

    return nlp,matcher

def annotate_text_inception(input_file_path, output_file_path, nlp, matcher):
    """Annotates text in CoNLL format and saves to file."""
    try:
        with open(input_file_path, "r", encoding="utf-8") as file:
            text = file.read()

        # Process text
        doc = nlp(text.lower())

        matches = matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            print(f"Matched soil depth: {span.text}")

        # Debugging: Print extracted entities
        for ent in doc.ents:
            print(f"Entity detected: {ent.text} - {ent.label_}")

        # Visualization (only if entities exist)
        if doc.ents:
            displacy.render(doc, style="ent", jupyter=True)
        else:
            print("No entities found in text.")

        # Create the CAS
        SENTENCE_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
        TOKEN_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
        NER_TYPE = "webanno.custom.TestLayer" # This is the Internal Name in the layer settings 

        # Load our type system
        with open(r"C:\Users\husain\pilot-uc-textmining-metadata\code\Bonares\full-typesystem.xml", "rb") as f:
            ts = load_typesystem(f)

        cas = Cas(typesystem=ts)
        cas.sofa_string = text

        Sentence = ts.get_type(SENTENCE_TYPE)
        Token = ts.get_type(TOKEN_TYPE)
        NamedEntity = ts.get_type(NER_TYPE)

        for sent in doc.sents:
            cas_sentence = Sentence(begin=sent.start_char, end=sent.end_char)
            cas.add(cas_sentence)  # Fix: Use `add()` instead of deprecated `add_annotation()`
            
            for token in sent:
                cas_token = Token(begin=token.idx, end=token.idx + len(token.text))
                cas.add(cas_token)

        for ent in doc.ents:
            cas_named_entity = NamedEntity(begin=ent.start_char, end=ent.end_char, value=ent.label_)
            cas.add(cas_named_entity)

        # Annotate soil depth matches
        for match_id, start, end in matches:
            span = doc[start:end]
            cas_named_entity = NamedEntity(begin=span.start_char, end=span.end_char, value="SOIL_DEPTH")
            cas.add(cas_named_entity)
            
            cas.to_xmi(output_file_path)
    except Exception as e:
        print(f"Error processing {input_file_path}: {e}")


def process_directory_inception(input_directory, output_directory, nlp, matcher):
    """Processes all text files in a directory and saves in CoNLL format."""
    input_directory = os.path.normpath(input_directory)
    output_directory = os.path.normpath(output_directory)

    os.makedirs(output_directory, exist_ok=True)  # Ensure output directory exists

    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):  # Process only text files
            input_file_path = os.path.join(input_directory, filename)
            output_file_path = os.path.join(output_directory, filename.replace(".txt", "_inception.xmi"))

            annotate_text_inception(input_file_path, output_file_path, nlp,matcher)

if __name__ == "__main__":

    # Initialize NLP with custom EntityRuler
    nlp,matcher = initialize_nlp_with_entity_ruler()

    # Define input/output paths
    input_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE_test"
    output_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE_test_annotated_inception"

    print(f"Processing text files in Inception format from: {input_directory}")
    process_directory_inception(input_directory, output_directory, nlp,matcher)
    print("✅ Inception annotation process completed.")
