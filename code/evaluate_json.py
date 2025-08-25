import spacy

# Load spaCy's small English model
nlp = spacy.load("en_core_web_sm")

def convert_json_to_bio(text, annotation_json):
    doc = nlp(text)
    tokens = [token.text for token in doc]
    labels = ["O"] * len(tokens)

    # Flatten all labeled 'value' fields from the nested JSON structure
    entity_spans = []

    # Process each category and its entities
    for category, entries in annotation_json.items():
        for item in entries:
            for sublabel, data in item.items():
                value = data.get("value", "")
                if value:
                    entity_spans.append({
                        "label": sublabel,
                        "value": value
                    })

    # Loop through the values and assign BIO tags
    for entity in entity_spans:
        label = entity["label"]
        value = entity["value"]

        # Search for the value in the text and assign BIO tags
        start_idx = text.find(value)
        
        while start_idx != -1:  # Continue as long as we find the value
            # Get the token indices for the value
            end_idx = start_idx + len(value)

            # Find the corresponding tokens that match the value in the doc
            token_start = token_end = -1
            for i, token in enumerate(doc):
                if token_start == -1 and token.idx == start_idx:
                    token_start = i  # First token of the match
                if token.idx + len(token.text) == end_idx:
                    token_end = i  # Last token of the match
                    break

            # Now assign BIO tags based on token positions
            if token_start != -1 and token_end != -1:
                for i in range(token_start, token_end + 1):
                    if i == token_start:
                        labels[i] = f"B-{label}"  # Beginning of the entity
                    else:
                        labels[i] = f"I-{label}"  # Inside the entity

            # Move to the next occurrence of the value in the text
            start_idx = text.find(value, start_idx + 1)

    return tokens, labels


# Example text input
text = """
Title: 
 Westerfeld: Long-term field trial on tillage and fertilization in crop rotation - PLOT
Abstract_text_1: 
 Westerfeld: Long-term field trial on tillage and fertilization in crop rotation - PLOT.
Abstract_text_2: 
 The long-term field trial started 1992 in Bernburg, Saxony-Anhalt, Germany (51°82' N, 11°70', 138 m above sea level). The soil is a loess chernozem over limestone with an effective rooting depth of 100 cm, containing 22% clay, 70% silt and 8% sand in the ploughed upper (Ap) horizon. It has a neutral pH (7.0–7.4) and an appropriate P and K supply (45–70 mg kg-1 and 130–185 mg kg-1 in calcium-acetate-lactate extract, respectively). The 1980–2010 annual average temperature was 9.7°C, and the average annual precipitation was 511 mm. On five large parcels in strip split plot design (1.2 ha each, main plots) the individual crops grain maize (Zea mays), winter wheat (Triticum aestivum), winter barley (Hordeum vulgare), winter rapeseed (Brassica napus ssp. napus), and winter wheat are rotated on the main plots and grown in parallel. All crop residues remain on the fields. Conservation tillage with a cultivator (CT; 10 cm flat non-inversion soil loosening) is compared to sub-plots with conventional tillage (MP; mould-board plough, carrier board with combined alternating ploughshares, ploughing depth 30 cm, incl. soil inversion). The differentially managed soils are either intensively (Int) operated according to usual practice regarding N supply and pesticide application or extensively managed (Ext) with reduced N supply, without fungicides, and growth regulators. The climate data are not included in the data set. They can be downloaded via the DWD's Open Data Server because there is a DWD weather station (ID 00445) in Bernburg-Strenzfeld. Description of table 1 Related datasets are listed in the metadata element 'Related Identifier'. Dataset version 1.0
Keywords: 
 Soil, nitrogen fertilizers, tillage, crop rotation, winter wheat, winter barley, rapeseed, maize, yields, topsoil, roots, rhizosphere, microbiomes, soil bacteria, soil fungi, arid zones, opendata, nitrogenous fertiliser, cultivation, yield (agricultural), Grossbeeren
"""

# JSON input (with 'value' for each entity)
annotation_json = {
  "Crops": [
    {
      "cropSpecies": {"value": "grain maize", "span": [110, 117]},
      "cropSpecies": {"value": "winter wheat", "span": [144, 151]},
      "cropSpecies": {"value": "winter barley", "span": [154, 162]},
      "cropSpecies": {"value": "winter rapeseed", "span": [165, 175]},
      "cropSpecies": {"value": "winter wheat", "span": [244, 251]}
    }
  ],
  "Soil": [
    {
      "soilTexture": {"value": "loess chernozem", "span": [64, 77]},
      "soilReferenceGroup": {"value": "chernozem", "span": [72, 79]},
      "soilDepth": {"value": "100 cm", "span": [115, 120]},
      "soilBulkDensity": {"value": "", "span": []},
      "soilPH": {"value": "7.0–7.4", "span": [147, 153]},
      "soilOrganicCarbon": {"value": "", "span": []},
      "soilAvailableNitrogen": {"value": "45–70 mg kg-1", "span": [177, 188]}
    }
  ],
  "Location": [
    {
      "country": {"value": "Germany", "span": [142, 147]},
      "region": {"value": "Saxony-Anhalt", "span": [126, 136]},
      "city": {"value": "Bernburg", "span": [119, 124]},
      "latitude": {"value": "51°82'", "span": [62, 68]},
      "longitude": {"value": "11°70'", "span": [70, 76]}
    }
  ],
  "Time Statement": [
    {
      "startTime": {"value": "1992", "span": [36, 39]},
      "endTime": {"value": "", "span": []},
      "duration": {"value": "", "span": []}
    }
  ]
}

tokens, labels = convert_json_to_bio(text, annotation_json)

# Print the results
for token, label in zip(tokens, labels):
    print(f"{token}: {label}")
