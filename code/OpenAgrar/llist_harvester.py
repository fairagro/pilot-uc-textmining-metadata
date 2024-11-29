"""
This file includes the different functions to harvest lists of publications and save them locally or share them
"""
import requests
import xmltodict
from processing import print_dict_tree

def oai_datacite_list(url = ''):
    assert url,"Error: No url was provided"
    # Make the GET request
    print(f'Recieved the url: {url}')
    list_of_ids = requests.get(url)
    json_response = xmltodict.parse(list_of_ids.text)
    # Convert to JSON for readability or further processing
    print(f'Keys of the json reponse are')
    print(print_dict_tree(json_response))
    token_continue = json_response['OAI-PMH']['ListRecords']['resumptionToken']['#text']
    base_url = url.split('&')[0]+"&resumptionToken="
    output_list = json_response['OAI-PMH']['ListRecords']['record']
    while token_continue:
        new_call = base_url + token_continue
        new_list_xml = requests.get(new_call)
        new_list_json = xmltodict.parse(new_list_xml.text)
        new_list_elements = new_list_json['OAI-PMH']['ListRecords']['record']
        try:
            token_continue = new_list_json['OAI-PMH']['ListRecords']['resumptionToken']['#text']
        except:
            output_list.extend(new_list_elements)
            print(f'Reached the end of the list, the number of captured values is {len(output_list)}')
            return output_list
        output_list.extend(new_list_elements)
        print(f"Loading in progress: {len(output_list)} has been loaded")
        if len(output_list) >= 1000000:
            break
    return output_list