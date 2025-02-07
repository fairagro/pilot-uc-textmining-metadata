import spacy
import json
import os
from spacy.matcher import Matcher
from spacy import displacy
from cassis import *
from cassis.typesystem import TYPE_NAME_FS_ARRAY, TYPE_NAME_ANNOTATION


def initialize_nlp_with_entity_ruler():
    model_name = "en_core_web_sm"
    species_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\species_list.json"
    soilTexture_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\soilTexture_list.json"
    bulkDensity_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\bulkDensity_list.json"

    nlp = spacy.load(model_name)
    nlp.disable_pipes("ner")

    def load_concept_list(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    species_list = load_concept_list(species_file)
    soilTexture_list = load_concept_list(soilTexture_file)
    bulkDensity_list = load_concept_list(bulkDensity_file)

    matcher = Matcher(nlp.vocab)

    depth_before_number = [
    {"LEMMA": "depth"},  # Ensures "depth" is present
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "of", "in")
    {"POS": "ADV", "OP": "*"},  # Optional adverbs (e.g., "approximately")
    {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "reaches")
    {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"LIKE_NUM": True},  # Matches the number (e.g., 100, 50)
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
]
    
    number_before_depth = [
    {"LIKE_NUM": True},  # Matches numbers (e.g., 100, 50)
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"POS": "NOUN", "OP": "*"},  # Optional nouns (e.g., "cm", "meters")
    {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "is", "has")
    {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "has been")
    {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"LEMMA": "depth"}  # Ensures "depth" is present
]

    depth_variants = [
        [{"LOWER": "soil"}, {"LOWER": "depth"}],  # Matches "soil depth"
        [{"LOWER": "depth"}]  # Matches "depth"
    ]

    matcher.add("soilDepth", [number_before_depth, depth_before_number])

    ruler = nlp.add_pipe("entity_ruler", before="parser")
    patterns = (
        sorted([
            {"label": "cropSpecies", "pattern": species}
            for species in species_list
        ], key=lambda x: -len(x["pattern"])) +
        sorted([
            {"label": "soilTexture", "pattern": soilTexture}
            for soilTexture in soilTexture_list
        ], key=lambda x: -len(x["pattern"])) +
        sorted([
            {"label": "soilBulkDensity", "pattern": bulkDensity}
            for bulkDensity in bulkDensity_list
        ], key=lambda x: -len(x["pattern"]))
    )
    ruler.add_patterns(patterns)

    return nlp, matcher

def annotate_text_inception(input_file_path, output_file_path, nlp, matcher):
    try:
        with open(input_file_path, "r", encoding="utf-8") as file:
            text = file.read()

        doc = nlp(text.lower())
        matches = matcher(doc)

        SENTENCE_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
        TOKEN_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
        NER_TYPE_CROPS = "webanno.custom.Crops"
        NER_TYPE_SOIL = "webanno.custom.Soil"

        with open(r"C:\Users\husain\pilot-uc-textmining-metadata\code\Bonares\full-typesystem.xml", "rb") as f:
            ts = load_typesystem(f)


        cas = Cas(typesystem=ts)
        cas.sofa_string = text

        # print(cas.typesystem.get_types())

        Sentence = ts.get_type(SENTENCE_TYPE)
        Token = ts.get_type(TOKEN_TYPE)
        CropsEntity = ts.get_type(NER_TYPE_CROPS)
        SoilEntity = ts.get_type(NER_TYPE_SOIL)

        # Add sentences and tokens to the CAS
        for sent in doc.sents:
            cas_sentence = Sentence(begin=sent.start_char, end=sent.end_char)
            cas.add(cas_sentence)

            for token in sent:
                cas_token = Token(begin=token.idx, end=token.idx + len(token.text))
                cas.add(cas_token)

        # Add entities to the CAS
        for ent in doc.ents:
            if ent.label_ == "cropSpecies":
                cas_named_entity = CropsEntity(begin=ent.start_char, end=ent.end_char, crops="cropSpecies")
            elif ent.label_ in ["soilTexture", "soilBulkDensity"]:
                cas_named_entity = SoilEntity(begin=ent.start_char, end=ent.end_char, Soil=ent.label_)
            else:
                continue
            cas.add(cas_named_entity)

        # Add soil depth matches to the CAS
        for match_id, start, end in matches:
            span = doc[start:end]
            # First, add the "depth" if it wasn't already added by the matcher
            depth_added = False
            
            for token in span:
                if token.lemma_ == "depth" and not depth_added:
                    # Add "depth" entity if it hasn't been added yet
                    cas_named_entity = SoilEntity(
                        begin=token.idx,
                        end=token.idx + len(token.text),  # Correct end position
                        Soil="soilDepth"
                    )
                    cas.add(cas_named_entity)
                    depth_added = True  # Mark that "depth" has been added
                    
                elif token.like_num:
                    # Annotate numbers associated with "depth"
                    cas_named_entity = SoilEntity(
                        begin=token.idx,
                        end=token.idx + len(token.text),  # Correct end position
                        Soil="soilDepth"
                    )
                    cas.add(cas_named_entity)

        cas.to_xmi(output_file_path)
    except Exception as e:
        print(f"Error processing {input_file_path}: {e}")


def process_directory_inception(input_directory, output_directory, nlp, matcher):
    input_directory = os.path.normpath(input_directory)
    output_directory = os.path.normpath(output_directory)

    os.makedirs(output_directory, exist_ok=True)

    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):
            input_file_path = os.path.join(input_directory, filename)
            output_file_path = os.path.join(output_directory, filename.replace(".txt", "_inception.xmi"))
            annotate_text_inception(input_file_path, output_file_path, nlp, matcher)

if __name__ == "__main__":
    nlp, matcher = initialize_nlp_with_entity_ruler()
    input_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE_test"
    output_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE_test_annotated_inception"

    print(f"Processing text files in Inception format from: {input_directory}")
    process_directory_inception(input_directory, output_directory, nlp, matcher)
    print("✅ Inception annotation process completed.")
