# the goal here is to search the species list for varieties and add them here
# also to remove these varieties from the species list

import json

# Define the path to the JSON file
file_path = "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/output/ConceptsList/species_list.json"  # Replace with your file path

# Open the file and load the JSON data
with open(file_path, 'r') as file:
    data = json.load(file)

# Initialize a new list to hold the "after var." entries
after_var_list = []

# Loop over the original list and process each entry
i = 0
l_list = []
seaonson_list = ["summer", "spring", "autumn", "fall", "season", "sommer", "herbst", "winter", "frühling", "herbst", "jahreszeit", "saison",
                 "vegetable", "fruit","grain","soft fruits"]  
while i < len(data):
    entry = data[i]
    skip=False
    for season in seaonson_list:
        if entry.startswith(season):
            data.pop(i)
            skip=True
            break
    if skip:
        continue
    if " var. " in entry:
        # Split the entry into two parts: before and after " var. "
        before_var = entry.split(" var. ")[0]
        after_var = entry.split(" var. ")[1]
        
        # Add the "before var." part to the original list (if not already)
        data.append(before_var)
        # Add the "after var." part to the new list
        after_var_list.append(after_var)
        after_var_list.append("var. " + after_var)  # Add "var. " prefix to the variety name
        
        # Remove the entry from the original list
        data.pop(i)  # Pop removes the item at the current index
    else:
        l_list.append(entry+" l.")
        i += 1  # Only increment if no modification was made (otherwise we skip over items)

# Save the modified original list (with "_modified" in the file name)
data.extend(l_list)
modified_file_name = "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/output/ConceptsList/species_list_modified.json"
with open(modified_file_name, 'w') as modified_file:
    json.dump(data, modified_file, indent=4)


new_file_name = "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/output/ConceptsList/varieties_list.json"
# Save the new list (after_var_list) to a file named "varieties_list.json"
with open(new_file_name, 'w') as new_file:
    json.dump(after_var_list, new_file, indent=4)
