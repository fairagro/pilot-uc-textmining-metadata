import spacy
import json
import os
from spacy.matcher import Matcher
from spacy import displacy
from cassis import *

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

    depth_pattern_1 = [
        {"LIKE_NUM": True},
        {"LOWER": "depth"}
    ]

    depth_pattern_2 = [
        {"LOWER": "depth"},
        {"LIKE_NUM": True}
    ]

    matcher.add("soilDepth", [depth_pattern_1, depth_pattern_2])

    ruler = nlp.add_pipe("entity_ruler")
    patterns = (
        [{"label": "cropSpecies", "pattern": [{"LOWER": species.lower()}]} for species in species_list] +
        [{"label": "soilTexture", "pattern": [{"LOWER": soilTexture.lower()}]} for soilTexture in soilTexture_list] +
        [{"label": "soilBulkDensity", "pattern": [{"LOWER": bulkDensity.lower()}]} for bulkDensity in bulkDensity_list]
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

        Sentence = ts.get_type(SENTENCE_TYPE)
        Token = ts.get_type(TOKEN_TYPE)
        CropsEntity = ts.get_type(NER_TYPE_CROPS)
        SoilEntity = ts.get_type(NER_TYPE_SOIL)

        for sent in doc.sents:
            cas_sentence = Sentence(begin=sent.start_char, end=sent.end_char)
            cas.add(cas_sentence)

            for token in sent:
                cas_token = Token(begin=token.idx, end=token.idx + len(token.text))
                cas.add(cas_token)

        for ent in doc.ents:
            if ent.label_ == "cropSpecies":
                cas_named_entity = CropsEntity(begin=ent.start_char, end=ent.end_char, value=ent.label_)
            elif ent.label_ in ["soilTexture", "soilBulkDensity"]:
                cas_named_entity = SoilEntity(begin=ent.start_char, end=ent.end_char, value=ent.label_)
            else:
                continue
            cas.add(cas_named_entity)

        for match_id, start, end in matches:
            for token in doc[start:end]:
                if token.like_num or token.lower_ == "depth":
                    cas_named_entity = SoilEntity(begin=token.idx, end=token.idx + len(token.text), value="soilDepth")
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
