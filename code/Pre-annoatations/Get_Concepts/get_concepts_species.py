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
    <http://aims.fao.org/aos/agrovoc/c_330074>
    <http://aims.fao.org/aos/agrovoc/c_8171>
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
    species = []
    # Execute the query and fetch the results
    try:
        results = sparql.query().convert()
        print("Query executed successfully.")

        # Print results in a readable format
        for result in results["results"]["bindings"]:
            hierarchical_type = result.get("hierarchicalType", {}).get("value", "")
            other_concept = result.get("otherConcept", {}).get("value", "")
            labelEn = result.get("labelEn", {}).get("value", "")
            species.append(labelEn.lower())
            labelDe = result.get("labelDe", {}).get("value", "")
            species.append(labelDe.lower())
        print(species)
    except Exception as e:
        print(f"An error occurred: {e}")
    return species


def save_species_list(species, filename=r"C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ConceptsList\species_list.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(species, f, ensure_ascii=False, indent=4)
    print(f"Species list saved to {filename}")

# After getting the species list
if __name__ == "__main__":
    species = keywords_from_agrovoc()
    save_species_list(species)
