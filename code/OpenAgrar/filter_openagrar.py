import json
import os
import pandas as pd
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # import file in the dataset place
    filename = os.getenv('DATAJSONFILE', 'default_value_if_not_set')
    # Open the file in write mode and use json.dump to write the list to the file
    with open(filename, "r") as file:
        opnenagrardata = json.load(file)
    print(f'the data was found and loaded!')
    print(f'Narrow down to articles from JKI and TI and separate the english and german language articles')
    #create a dataframe to store all the data
    df = pd.DataFrame(columns=["ID", "title", "abstract_text","publisher", "publication_year","institute",
                               "authors_names","subjects","language"])

    for element in opnenagrardata:
        try:
            # Access abstract text
            description = element['metadata']['resource']['descriptions']['description']
            if isinstance(description, list):
                abstract_text = ""
                for desc in description:
                    if desc['@descriptionType'] == 'Abstract':
                        abstract_text = desc["#text"]
                        break
                if abstract_text == "":
                    continue
            else:
                if description['@descriptionType'] == 'Abstract':
                    abstract_text = desc["#text"]
                else:
                    continue

            abstract_text = abstract_text.replace('\n',  ' ')
            abstract_text = '"'+abstract_text+'"'
            # Access authors' names
            authors_names = element["metadata"]["resource"]["creators"]["creator"]
            # Access publisher
            publisher = element["metadata"]["resource"]["publisher"]
            pub_year = element["metadata"]["resource"]['publicationYear']
            # Access language
            language = element["metadata"]["resource"]["language"]
            # Access title
            title = element["metadata"]["resource"]["titles"]["title"]
            subjects = element["metadata"]["resource"]["subjects"]["subject"]
            if isinstance(title, str):
                title = title
            else:
                title = title['#text']
            id = element["header"]["identifier"].split("_")[-1]
            institute = ""
            # Extract 'ti' from 'institute:ti' in 'setSpec'
            institute = None
            for item in element['header']['setSpec']:
                if item.startswith('institute:'):
                    institute = item.split(':')[1]  # Split and take the part after 'institute:'
                    break
        except:
            continue
            # Append the extracted data as a new row to the DataFrame
        df.loc[len(df)] = [id, title, abstract_text, publisher, pub_year,institute,authors_names, subjects,language]
    #save the dataset as a csv
    filename = os.getenv('DATACSVFILE', 'default_value_if_not_set')
    df.to_csv(filename, encoding="utf-8", index=False, sep='|')




