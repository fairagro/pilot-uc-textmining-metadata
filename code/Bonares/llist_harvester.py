"""
This file includes the different functions to harvest lists of publications and save them locally or share them
"""
import requests
import xmltodict
from processing import print_dict_tree
import tqdm

def oai_datacite_list(url = ''):
    assert url,"Error: No url was provided"
    # Make the GET request
    print(f'Recieved the url: {url}')
    list_of_ids = requests.get(url)

    #save a list of all the html datasets urls in a json format
    list_of_docs = list_of_ids.json()["response"]["docs"]

    # get a list of xml urls
    xml_urls = get_xml_list(list_of_docs)


    # Convert to JSON for readability or further processing
    #print(f'Keys of the json reponse are')
    dataset = requests.get(xml_urls[1])
    dataset = xmltodict.parse(dataset.text)
    #print(print_dict_tree(dataset))
    output_list = []

    # make requests for each dataset and save it
    for url in tqdm.tqdm(xml_urls):
        try:
            dataset = requests.get(url)
            json_response = xmltodict.parse(dataset.text)
            output_list.append(json_response)
        except:
            print(f'nonvalid url: {url}')


    return output_list

def get_xml_list(docs):
    """
    This function takes the list of docs of the datasets and modify them to fit the format
    "https://maps.bonares.de/finder/resources/dataform/xml/[id]" which can be used to get the
    metadata of each dataset mentioned in this list
    :param docs: a list of documents with their types and ids
    :return: A list of the xml urls in format: "https://maps.bonares.de/finder/resources/dataform/xml/[id]"
    """
    base_url = "https://maps.bonares.de/finder/resources/dataform/xml/"

    # convert the html url list to a list of ids that could be attached to the base url
    xml_list = []
    for doc in docs:
        id = doc['id']
        xml_list.append(base_url+id)
    return xml_list
