import json
import sys

import requests
from lxml import etree as ET


def parse_identification(identification, crate: dict, namespaces: dict):
    title = (
        identification.find("gmd:citation", namespaces)
        .find("gmd:CI_Citation", namespaces)
        .find("gmd:title", namespaces)
        .find("gco:CharacterString", namespaces)
        .text
    )
    crate["name"] = title

    abstract_n = identification.find("gmd:abstract", namespaces)
    try:
        abstract = abstract_n.find("bnr:TypedCharacterString", namespaces).text
    except AttributeError:
        abstract = abstract_n.find("gco:CharacterString", namespaces).text
    crate["description"] = abstract

    keywords = []
    keywords_node = (
        identification.find("gmd:descriptiveKeywords", namespaces)
        .find("gmd:MD_Keywords", namespaces)
        .findall("gmd:keyword", namespaces)
    )
    for keyword in keywords_node:
        try:
            anchor = keyword.find("gmx:Anchor", namespaces)
            if "{http://www.w3.org/1999/xlink}href" in anchor.attrib:
                term = anchor.attrib["{http://www.w3.org/1999/xlink}href"]
                keywords.append(term)
                # TODO: consider using DefinedTerm? Or schema:URI type?
            else:
                keywords.append(anchor.text)
        except AttributeError:
            keywords.append(
                keyword.find("gco:CharacterString", namespaces).text
            )
    crate["keywords"] = keywords


def harvest_bonares_resource_to_rocrate_json(bonares_id: str):
    url = f"https://maps.bonares.de/finder/resources/dataform/xml/{bonares_id}"

    res = requests.get(url)

    if res.status_code != 200:
        raise ValueError(f"Failed to fetch {url}")

    namespaces = {
        "gmd": "http://www.isotc211.org/2005/gmd",
        "gco": "http://www.isotc211.org/2005/gco",
        "bnr": "http://www.bonares.de/gmd",
        "gmx": "http://www.isotc211.org/2005/gmx",
        "xlink": "http://www.w3.org/1999/xlink",
    }
    doc = ET.fromstring(res.content)

    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@type": "Dataset",
        "@id": url,
    }

    date_stamp = doc.find("gmd:dateStamp", namespaces)
    if date_stamp is not None:
        crate["datePublished"] = date_stamp.find("gco:Date", namespaces).text
    identification_info = doc.find("gmd:identificationInfo", namespaces)
    bnr_identification = identification_info.find(
        "bnr:MD_DataIdentification", namespaces
    )
    if bnr_identification is not None:
        print("Found bonares specific metadata")
        parse_identification(bnr_identification, crate, namespaces)
        columns = (
            bnr_identification.find("bnr:dataSchema", namespaces)
            .find("bnr:MD_DataSchema", namespaces)
            .findall("bnr:column", namespaces)
        )

        additional_properties = []
        for column_n in columns:
            prop_def = {
                "@type": "PropertyValue",
                "additionalType": "MaterialAttributeValue",
            }

            column = column_n.find("bnr:MD_Column", namespaces)
            name = (
                column.find("bnr:name", namespaces)
                .find("gco:CharacterString", namespaces)
                .text
            )
            print_line = [name]
            long_name_n = column.find("bnr:longName", namespaces)
            if long_name_n is not None:
                long_name = long_name_n.find(
                    "gco:CharacterString", namespaces
                ).text
                print_line.append(long_name)
                prop_def["name"] = long_name
                prop_def["additionalName"] = name
            else:
                prop_def["name"] = name
            description_n = column.find("bnr:description", namespaces)
            if description_n is not None:
                description = description_n.find(
                    "gco:CharacterString", namespaces
                ).text
                print_line.append(description)
                prop_def["description"] = description

            additional_properties.append(prop_def)

        lab_process = {
            "@type": "https://bioschemas.org/LabProcess",
            "object": [
                {
                    "@type": "https://bioschemas.org/Sample",
                    "additionalProperty": additional_properties,
                }
            ],
        }
        crate["about"] = [lab_process]
    else:
        identification = identification_info.find(
            "gmd:MD_DataIdentification", namespaces
        )
        if identification is None:
            identification = identification_info.find(
                "bnr:SV_ServiceIdentification", namespaces
            )
        if identification is not None:
            parse_identification(identification, crate, namespaces)
    return crate


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Missing Bonares ID")
    bonares_id = sys.argv[1]
    crate = harvest_bonares_resource_to_rocrate_json(bonares_id)
    print(json.dumps(crate, indent=2))
