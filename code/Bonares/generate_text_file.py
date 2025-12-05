import json
import os
import pandas as pd
# Press the green button in the gutter to run the script.

# Function to extract the keywords
def extract_keywords(data):
    keywords = []
    if isinstance(data, list):  # Handle if `data` is a list
        for entry in data:
            md_keywords = entry.get('gmd:MD_Keywords', {})
            gmd_keyword_list = md_keywords.get('gmd:keyword', [])
            for keyword in gmd_keyword_list:
                if 'gmx:Anchor' in keyword:
                    keywords.append(keyword['gmx:Anchor']['#text'])
                elif 'gco:CharacterString' in keyword:
                    keywords.append(keyword['gco:CharacterString'])
    elif isinstance(data, dict):  # Handle if `data` is a dictionary
        md_keywords = data.get('gmd:MD_Keywords', {})
        gmd_keyword_list = md_keywords.get('gmd:keyword', [])
        for keyword in gmd_keyword_list:
            if 'gmx:Anchor' in keyword:
                keywords.append(keyword['gmx:Anchor']['#text'])
            elif 'gco:CharacterString' in keyword:
                keywords.append(keyword['gco:CharacterString'])
    return keywords

if __name__ == '__main__':
        # Open the file in write mode and use json.dump to write the list to the file
    with open("/Users/husain/pilot-uc-textmining-metadata/data/Bonares/dataset_files/dataset_files.json", "r") as file:
        bonares = json.load(file)
    print(f'the data was found and loaded!')

    count = 0
    valid_count = 0
    file_count = 0
    for element in bonares:
        # Initialize variables to None
        abstract_text = None
        descriptive_keywords = None
        title = None
        id = None

        # Access each field with its own try block
        try:
            # Access abstract text
            abstract_text = element['gmd:MD_Metadata']['gmd:identificationInfo']['bnr:MD_DataIdentification'][
                'gmd:abstract']['bnr:TypedCharacterString']['#text']
            valid_count+=1

        except Exception as e:
            print(f"Error accessing abstract_text: {e}")
            count+=1


        try:
            # Access keywords
            descriptive_keywords  = element['gmd:MD_Metadata']["gmd:identificationInfo"]["bnr:MD_DataIdentification"][
                "gmd:descriptiveKeywords"]
            print(descriptive_keywords)
            # keywords = extract_keywords(descriptive_keywords)
            # print(keywords)
            valid_count+=1
            break

        except Exception as e:
            print(f"Error accessing key_words: {e}")
            # keywords = None  # Ensure keywords is defined even if there's an error
            count += 1


        try:
            # Access title
            title = element['gmd:MD_Metadata']['gmd:identificationInfo']["bnr:MD_DataIdentification"]["gmd:citation"][
                "gmd:CI_Citation"]["gmd:title"]['gco:CharacterString']
            valid_count+=1

        except Exception as e:
            print(f"Error accessing title: {e}")
            count+=1


        try:
            # Access id
            id = element['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString']['#text']
            valid_count+=1
        except Exception as e:
            print(f"Error accessing id: {e}")
            count+=1
        
        if id is not None:
            if abstract_text is not None or descriptive_keywords is not None or title is not None:
                filename = f"/Users/husain/pilot-uc-textmining-metadata/data/Bonares/dataset_files/text_files/{id}.txt"

                # cleaned_keywords = None
                # if keywords is not None:
                #     cleaned_keywords = [kw for kw in keywords if isinstance(kw, str)]

                # Construct the content
                content = f"Title:\n{title}\n\n"
                content += f"Abstract:\n{abstract_text}\n\n"
                content += f"Keywords:\n{descriptive_keywords}"
                
                # Create and write to the file
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f"Created file: {filename}")
                file_count+=1

    print(f"Valid count: {valid_count/4}")
    print(f"count: {count/4}")
    print(f"created {file_count} files")





