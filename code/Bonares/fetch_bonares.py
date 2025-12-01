import json
from llist_harvester import oai_datacite_list
import os
import requests
from draft_bonares_to_rocrate import harvest_bonares_resource_to_rocrate_json
import xmltodict
# Press the green button in the gutter to run the script.
def get_json_dataset(url):
    data = requests.get(url)
    json_data = xmltodict.parse(data.text)
    return json_data


if __name__ == '__main__':
    url = os.getenv('BONARES_URL', 'default_value_if_not_set')

    # Parse arguments
    #args = parser.parse_args()
    bonares_list = oai_datacite_list(str(url))

    filename = os.getenv('DATAJSONFILE', 'default_value_if_not_set')
    # Open the file in write mode and use json.dump to write the list to the file

    ro_crates = []
    res = requests.get(str(url))
    for i, doc in enumerate(res.json()["response"]["docs"]):
        bonares_id = doc["id"]
        print(f"Harvesting dataset {i}")
        ro_crate = harvest_bonares_resource_to_rocrate_json(bonares_id)
        ro_crates.append(ro_crate)

    with open(filename, "wt") as file:
        file.write(json.dumps(bonares_list))