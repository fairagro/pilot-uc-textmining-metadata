import ast
import argparse
import os
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import json
def keywords_from_agrovoc():


    # Define the SPARQL endpoint
    sparql_endpoint = "https://agrovoc.fao.org/sparql"

    # Define the SPARQL query
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>

SELECT DISTINCT ?hierarchicalType ?otherConcept ?labelEn ?labelDe
WHERE { 
  VALUES ?concept {
    <http://aims.fao.org/aos/agrovoc/c_7199>
  }

  # Follow skos:narrower recursively (any depth)
  ?concept skos:narrower+ ?otherConcept .
  BIND("narrower" AS ?hierarchicalType)

  # Get English label if available
  OPTIONAL { 
    ?otherConcept skosxl:prefLabel/skosxl:literalForm ?labelEn.
    FILTER(langMatches(lang(?labelEn), "en"))
  }

  # Get German label if available
  OPTIONAL { 
    ?otherConcept skosxl:prefLabel/skosxl:literalForm ?labelDe.
    FILTER(langMatches(lang(?labelDe), "de"))
  }
}
    """

    # Set up the SPARQL wrapper
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    soilTexture = []
    # Execute the query and fetch the results
    try:
        results = sparql.query().convert()
        print("Query executed successfully.")

        # Print results in a readable format
        for result in results["results"]["bindings"]:
            hierarchical_type = result.get("hierarchicalType", {}).get("value", "")
            other_concept = result.get("otherConcept", {}).get("value", "")
            labelEn = result.get("labelEn", {}).get("value", "")
            soilTexture.append(labelEn.lower())
            labelDe = result.get("labelDe", {}).get("value", "")
            soilTexture.append(labelDe.lower())
    except Exception as e:
        print(f"An error occurred: {e}")
    return soilTexture


def save_soilTexture_list(soilTexture, filename=r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\soilTexture_list.json"):
    predefined_soil_texture = ["Clay","Lehm", "Silty clay","Schluffiger Ton", "Sandy clay","Sandiger Ton", "Clay loam","Lehmboden", "Sandy clay loam","Sandiger lehmiger Lehm", "Silty clay loam","Schluffiger Tonlehm", "Loam","Lehm", "Sandy loam","Sandiger Lehm", "Silty loam","Schluffiger Lehm", "Sand","Sand", "Loamy sand","Lehmiger Sand", "Silt","Schlick"]
    predefined_soil_texture = [item.lower() for item in predefined_soil_texture]
    soilTexture.extend(predefined_soil_texture)
    print(soilTexture)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(soilTexture, f, ensure_ascii=False, indent=4)
    print(f"soilTexture list saved to {filename}")

# After getting the species list
if __name__ == "__main__":
    soilTexture = keywords_from_agrovoc()
    save_soilTexture_list(soilTexture, "/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/output/ConceptsList/soilTexture_list.json")
