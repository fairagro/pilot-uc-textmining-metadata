import json
import os
import pandas as pd
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # import file in the dataset place
    filename = os.getenv('DATAJSONFILE', 'default_value_if_not_set')
    # Open the file in write mode and use json.dump to write the list to the file
    with open(filename, "r") as file:
        bonares = json.load(file)
    print(f'the data was found and loaded!')
    #create a dataframe to store all the data
    df = pd.DataFrame(columns=["ID", "title", "abstract_text","keywords", "publication_year","institute",
                               "language", "location"])

    for element in bonares:
        # Initialize variables to None
        abstract_text = None
        key_words = None
        pub_year = None
        language = None
        title = None
        location = None
        id = None
        institute = None

        # Access each field with its own try block
        try:
            # Access abstract text
            abstract_text = element['gmd:MD_Metadata']['gmd:identificationInfo']['bnr:MD_DataIdentification'][
                'gmd:abstract']['bnr:TypedCharacterString']['#text']
        except Exception as e:
            print(f"Error accessing abstract_text: {e}")

        try:
            # Access keywords
            key_words = element['gmd:MD_Metadata']["gmd:identificationInfo"]["bnr:MD_DataIdentification"][
                "gmd:descriptiveKeywords"]
        except Exception as e:
            print(f"Error accessing key_words: {e}")

        try:
            # Access publication year
            pub_year = \
            element['gmd:MD_Metadata']['gmd:identificationInfo']["bnr:MD_DataIdentification"]["gmd:citation"][
                "gmd:CI_Citation"]["gmd:title"]
        except Exception as e:
            print(f"Error accessing pub_year: {e}")

        try:
            # Access language
            language = element["gmd:MD_Metadata"]["gmd:language"]["LanguageCode"]["@codeListValue"]
        except Exception as e:
            print(f"Error accessing language: {e}")

        try:
            # Access title
            title = element['gmd:MD_Metadata']['gmd:identificationInfo']["bnr:MD_DataIdentification"]["gmd:citation"][
                "gmd:CI_Citation"]["gmd:title"]['gco:CharacterString']
        except Exception as e:
            print(f"Error accessing title: {e}")

        try:
            # Access location
            location = element['gmd:MD_Metadata']["gmd:identificationInfo"]["bnr:MD_DataIdentification"]['gmd:extent']
        except Exception as e:
            print(f"Error accessing location: {e}")

        try:
            # Access id
            id = element['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString']['#text']
        except Exception as e:
            print(f"Error accessing id: {e}")

        try:
            # Access institute
            institute = element['gmd:MD_Metadata']["gmd:contact"]["gmd:CI_ResponsibleParty"]["gmd:organisationName"][
                "gco:CharacterString"]["#text"]
        except Exception as e:
            print(f"Error accessing institute: {e}")
            # Append the extracted data as a new row to the DataFrame
        df.loc[len(df)] = [id, title, abstract_text, key_words, pub_year,institute, language, location]
    #save the dataset as a csv
    filename = os.getenv('DATACSVFILE', 'default_value_if_not_set')
    excel_filename = os.getenv('DATAEXCELFILE', 'default_value_if_not_set')
    df.to_csv(filename, encoding="utf-8", index=False, sep='|')
    df.to_excel(excel_filename, index=False)




