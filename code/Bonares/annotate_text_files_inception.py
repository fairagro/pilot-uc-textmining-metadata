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
    organicCarbon_file = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\organicCarbon_list.json"

    
    nlp = spacy.load(model_name)
    nlp.disable_pipes("ner")

    def load_concept_list(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    species_list = load_concept_list(species_file)
    soilTexture_list = load_concept_list(soilTexture_file)
    bulkDensity_list = load_concept_list(bulkDensity_file)
    organicCarbon_list = load_concept_list(organicCarbon_file)


    matcher = Matcher(nlp.vocab)

    depth_before_number = [
    {"LEMMA": "depth"},  # Ensures "depth" is present
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "of", "in")
    {"POS": "ADV", "OP": "*"},  # Optional adverbs (e.g., "approximately")
    {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "reaches")
    {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"LIKE_NUM": True},  # Matches the number (e.g., 100, 50) - Optional now
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
]
    
    number_before_depth = [
    {"LIKE_NUM": True},  # Matches numbers (e.g., 100, 50) - Optional now
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"POS": "NOUN", "OP": "*"},  # Optional nouns (e.g., "cm", "meters")
    {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "is", "has")
    {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "has been")
    {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
    {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
    {"LEMMA": "depth"}  # Ensures "depth" is present
]

    ph_before_number = [
        {"LEMMA": "ph"},  # Match "ph" as a separate entity
        {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation before the number (e.g., "(")
        {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "of", "in")
        {"POS": "ADV", "OP": "*"},  # Optional adverbs (e.g., "approximately")
        {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "reaches")
        {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
        {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation (e.g., "-")
        {"LIKE_NUM": True, "TEXT": {"REGEX": r"^(?:[0-9]|1[0-4])(\.\d+)?$"}},  # Match single pH values like "7.0" or "7.4"
        {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation (e.g., "-")
        {"LIKE_NUM": True, "TEXT": {"REGEX": r"^(?:[0-9]|1[0-4])(\.\d+)?$"}},  # Match the second pH value for ranges (e.g., "7.0" or "7.4")
        {"IS_PUNCT": True},  # Optional punctuation after the number (e.g., ")")
    ]

    ph_before_number_1 = [
    {"LEMMA": "ph"},  # Match "ph" as a separate entity
    {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "of", "in")
    {"POS": "ADV", "OP": "*"},  # Optional adverbs (e.g., "approximately")
    {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "reaches")
    {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
    {"LIKE_NUM": True, "TEXT": {"REGEX": r"^\d+(\.\d+)?$"}},  # Match whole numbers and decimals (e.g., "6", "6.0", "7.4")
]

    number_before_ph = [
        {"LIKE_NUM": True, "TEXT": {"REGEX": r"^(?:[0-9]|1[0-4])(\.\d+)?$"}},  # Match single pH values like "7.0" or "7.4"
        {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
        {"LIKE_NUM": True, "TEXT": {"REGEX": r"^(?:[0-9]|1[0-4])(\.\d+)?$"}, "OP": "*"},  # Match single pH values like "7.0" or "7.4"
        {"POS": "NOUN", "OP": "*"},  # Optional nouns (e.g., "cm", "meters")
        {"POS": "ADP", "OP": "*"},  # Optional prepositions (e.g., "is", "has")
        {"POS": "VERB", "OP": "*"},  # Optional verbs (e.g., "is", "has been")
        {"POS": "DET", "OP": "*"},  # Optional determiners (e.g., "the")
        {"IS_PUNCT": True, "OP": "*"},  # Optional punctuation
        {"LEMMA": "ph"}  # Match "pH" as a separate entity
    ]

    depth_variants = [
        [{"LOWER": "soil"}, {"LOWER": "depth"}],  # Matches "soil depth"
        [{"LOWER": "depth"}]  # Matches "depth"
    ]

    soil_available_nitrogen_pattern = [
    # Matches phrases like "plant nitrogen (N) availability"
    [
        {"LOWER": "plant", "OP": "?"},  # Optional "plant"
        {"LOWER": "nitrogen"},  # Mandatory "nitrogen"
        {"TEXT": "(", "OP": "?"},  # Optional opening bracket
        {"LOWER": "n", "OP": "?"},  # Optional chemical symbol (N)
        {"TEXT": ")", "OP": "?"},  # Optional closing bracket
        {"LOWER": "availability"}  # Mandatory "availability"
    ],
    # Matches phrases like "available nitrogen" or "nitrogen availability"
    [
        {"LOWER": "available", "OP": "?"},  # Optional "available"
        {"LOWER": "nitrogen"},  # Mandatory "nitrogen"
        {"LOWER": "availability", "OP": "?"}  # Optional "availability"
    ]
]

    matcher.add("soilDepth", [number_before_depth, depth_before_number])
    matcher.add("soilPH", [number_before_ph, ph_before_number_1, ph_before_number])
    matcher.add("soilAvailableNitrogen", soil_available_nitrogen_pattern)



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
        ], key=lambda x: -len(x["pattern"])) +
        sorted([
            {"label": "soilOrganicCarbon", "pattern": organicCarbon}
            for organicCarbon in organicCarbon_list
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
            elif ent.label_ in ["soilTexture", "soilBulkDensity", "soilOrganicCarbon"]:
                cas_named_entity = SoilEntity(begin=ent.start_char, end=ent.end_char, Soil=ent.label_)
            else:
                continue
            cas.add(cas_named_entity)

        # Add soil depth matches to the CAS
        for match_id, start, end in matches:
            span = doc[start:end]
            depth_added = False
            ph_added = False
            nitrogen_added = False
            for token in span:
                if token.lemma_ in ["depth", "ph", "availability"] and not (
                    depth_added if token.lemma_ == "depth" else ph_added if token.lemma_ == "ph" else nitrogen_added
                ):
                    # Determine the correct annotation
                    soil_type = (
                        "soilDepth" if token.lemma_ == "depth" else
                        "soilPH" if token.lemma_ == "ph" else
                        "soilAvailableNitrogen"
                    )

                    # Add the annotation
                    cas_named_entity = SoilEntity(
                        begin=token.idx,
                        end=token.idx + len(token.text),  # Correct end position
                        Soil=soil_type
                    )
                    cas.add(cas_named_entity)

                    # Mark as added to prevent duplicate annotations
                    if token.lemma_ == "depth":
                        depth_added = True
                    elif token.lemma_ == "ph":
                        ph_added = True
                    else:
                        nitrogen_added = True

                elif token.like_num:
                    # Annotate numbers associated with depth, pH, or nitrogen availability
                    if any(t.lemma_ in ["depth", "ph", "availability"] for t in span):
                        soil_type = (
                            "soilDepth" if "depth" in [t.lemma_ for t in span] else
                            "soilPH" if "ph" in [t.lemma_ for t in span] else
                            "soilAvailableNitrogen"
                        )

                        cas_named_entity = SoilEntity(
                            begin=token.idx,
                            end=token.idx + len(token.text),  # Correct end position
                            Soil=soil_type
                        )
                        cas.add(cas_named_entity)

        if len(doc.ents) > 0:
            cas.to_xmi(output_file_path)
            return True 
        else:
            return False 
    except Exception as e:
        print(f"Error processing {input_file_path}: {e}")


def process_directory_inception(input_directory, output_directory, nlp, matcher):
    input_directory = os.path.normpath(input_directory)
    output_directory = os.path.normpath(output_directory)

    os.makedirs(output_directory, exist_ok=True)

    i = 0
    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):
            input_file_path = os.path.join(input_directory, filename)
            output_file_path = os.path.join(output_directory, filename.replace(".txt", "_inception.xmi"))
            entity_present = annotate_text_inception(input_file_path, output_file_path, nlp, matcher)
            if(entity_present):
                i = i+1
            if i == 15:
                break

if __name__ == "__main__":
    nlp, matcher = initialize_nlp_with_entity_ruler()
    input_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE"
    output_directory = r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\filtered_df_soil_crop_year_LTE_test_annotated_inception_15"

    print(f"Processing text files in Inception format from: {input_directory}")
    process_directory_inception(input_directory, output_directory, nlp, matcher)
    print("✅ Inception annotation process completed.")
