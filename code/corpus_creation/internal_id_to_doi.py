"""
This file include the functions required to get the doi of a dataset for eachof Bonares and Openagrar datasets
"""

import json

def id_to_doi_bonares(id_, bonares_dict):
    """
    Map BonaRes internal ID → DOI.
    bonares_dict = already-loaded JSON list
    """
    for entry in bonares_dict:
        if id_ == entry["identifier"][0]:
            doi = entry["identifier"][1]
            if "Child" in doi:
                doi = doi.split("set ")[-1]
            return doi
    return None

def id_to_doi_openagrar(id_, openagrar_dict):
    """
    Map OpenAgrar internal ID → DOI.
    openagrar_dict = already-loaded JSON list
    """
    for entry in openagrar_dict:
        try:
            if id_ in entry["mainEntityOfPage"]:
                for ident in entry["identifier"]:
                    if ident.get("propertyID") == "doi":
                        return ident["value"]
                return entry["identifier"][0]["value"]  # fallback
        except:
            continue
    print(f"No id found for {id_}")
    return None

def map_doi(row, bonares_dict, openagrar_dict):
    """
    Row-level DOI resolver.
    Uses row['source'] and row['file_name'].
    """
    file_id = row["file_name"].split(".")[0]

    if row["source"] == "BonaRes":
        return id_to_doi_bonares(file_id, bonares_dict)

    elif row["source"] == "OpenAgrar":
        return id_to_doi_openagrar(file_id, openagrar_dict)

    return None

def load_dataset_dict(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
