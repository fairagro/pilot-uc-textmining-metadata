import json
import pandas as pd
german_city_names = set()
types = ["PPLA","PPLA2","PPLC", "PPLL","PPL"]
rejected = ["boden", "see", "panten", "wanna","sand","felden","felde", "eisen"
            ,"bark","below","block","berl","during","point", "bias","over","may","well"
            ,"end","drift", "hand","wetter","grain","grass","bone","theta","along","wind",
            "rain", "einem","einer","eines","einem","einen","eines","einer","einem","besten",
            "berk","drei","holz","trotz","dies", "achim","raum","feld","lage","heidlamp","dechow"]
with open("/home/abdelmalak/Documents/DE.txt", "r", encoding="utf-8") as file:
    for line in file:
        parts = line.strip().split("\t")
        if len(parts) > 1:
            name = parts[2]
            if not name.lower() in rejected and not parts[1].lower() in rejected:
                type = parts[7]
                if type in types:
                    german_city_names.add(name.lower())
                    german_city_names.add(parts[1].lower())
                    if name.lower() == "berk":
                        print(parts)
                    if " " in name:
                        hyphenated_name = name.replace(" ", "-")
                        german_city_names.add(hyphenated_name.lower())

# Convert to list if needed
german_city_names = list(german_city_names)

# filename = "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/dataset_files/ConceptsList/de_cities_list.json"
# with open(filename, "w", encoding="utf-8") as f:
#         json.dump(german_city_names, f, ensure_ascii=False, indent=4)

# import pandas as pd

# Path to your Excel file
file_path = "/home/abdelmalak/Documents/Mappe2.csv"

# Load the Excel file
df = pd.read_csv(file_path, header=None, encoding='ISO-8859-1')

# Convert the single column to a list
column_as_list = df[0].tolist()  # Column 0 since there's only one column

for i in column_as_list:
    german_city_names.append(i.lower())
    if " " in i:
        hyphenated_name = i.replace(" ", "-")
        german_city_names.append(hyphenated_name.lower())
filename = "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/output/ConceptsList/de_cities_list.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(german_city_names, f, ensure_ascii=False, indent=4)