from spacy.lang.en import English

# If you're using strings, convert them to token pattern format
def make_soil_patterns(soil_textures):
    patterns = []
    for texture in soil_textures:
        # e.g., texture = "loamy sand" -> ["loamy", "sand"]
        words = texture.split()
        token_pattern = [{"LOWER": {"IN": ["weak", "strong", "fine", "compact", "very", "highly","heavy","light"]}, "OP": "*"}]  # allow any number of adj/adv
        token_pattern += [{"LOWER": w.lower()} for w in words]
        patterns.append({"label": "soilTexture", "pattern": token_pattern})
    return sorted(patterns, key=lambda x: -len(x["pattern"]))

# If you're using strings, convert them to token pattern format
def make_soil_referencegroup(soil_refgroups):
    patterns = []
    for ref_group in soil_refgroups:
        # e.g., texture = "loamy sand" -> ["loamy", "sand"]
        words = ref_group.split()
        list_adjs=[
    "haplic",
    "arenic",
    "loamy",
    "silty",
    "clayey",
    "sandy",
    "peaty",
    "chalky",
    "saline",
    "acidic",
    "alkaline",
    "compact",
    "dry",
    "moist",
    "fertile",
    "infertile",
    "well-drained",
    "poorly-drained",
    "aerated",
    "rich",
    "stony",
    "gravelly",
    "heavy",
    "light",
    "crumbly",
    "muddy",
    "crumbling",
    "fractal",
    "alluvial",
    "flooded",
    "eroded",
    "arid",
    "forest",
    "wet",
    "turbid",
    "barren",
    "subsoil",
    "gleyic",
    "luvic",
    "chernozemic",
    "andosolic",
    "podzolic",
    "vertic",
    "fluvisolic",
    "calcareous",
    "ferrallitic",
    "alfisolic",
    "cambic",
    "regosolic"
]
        token_pattern = [{"LOWER": {"IN": list_adjs}, "OP": "*"}]  # allow any number of adj/adv
        token_pattern += [{"IS_PUNCT": True, "OP": "?"}]
        token_pattern += [{"LOWER": w.lower()} for w in words]
        patterns.append({"label": "soilReferenceGroup", "pattern": token_pattern})
    return sorted(patterns, key=lambda x: -len(x["pattern"]))