import json
import sys

import requests

from draft_bonares_to_rocrate import harvest_bonares_resource_to_rocrate_json

if __name__ == "__main__":
    ro_crates = []
    max = "2000"
    if len(sys.argv) >= 2:
        max_str = sys.argv[1]
        if max_str.isnumeric():
            max = max_str
    res = requests.get(
        f"https://maps.bonares.de/finder/core0/select?q=*&wt=json&fl=id,type&start=0&rows={max}"
    )
    for i, doc in enumerate(res.json()["response"]["docs"]):
        bonares_id = doc["id"]
        print(f"Harvesting dataset {i}")
        print(doc["type"])
        ro_crate = harvest_bonares_resource_to_rocrate_json(bonares_id)
        ro_crates.append(ro_crate)

    with open("result.json", "wt") as file:
        file.write(json.dumps({"@graph": ro_crates}))
