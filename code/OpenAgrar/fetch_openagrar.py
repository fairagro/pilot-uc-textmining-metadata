import json
from llist_harvester import oai_datacite_list
import os
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    url = os.getenv('OPENAGRAR_URL', 'default_value_if_not_set')

    # Parse arguments
    #args = parser.parse_args()
    openagrar_list = oai_datacite_list(str(url))

    filename = os.getenv('DATAJSONFILE', 'default_value_if_not_set')
    # Open the file in write mode and use json.dump to write the list to the file
    with open(filename,"w", encoding="utf-8") as file:
        json.dump(openagrar_list, file)