# Experimental use case: Harvesting domain specific metadata fields from Bonares repository.

This folder contains scripts to harvest metadata from Bonares datasets, transform then into schema.org/RO-Crate `json-ld` files and, optionally, inspect the use of domain specific variables.


## Installation and use
1. Recommended is to create a Python virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

2. Install Python dependencies
```bash
pip install -r draft-bonares-to-rocrate.requirements.txt
```

3. Run the harvesting code
```bash
python draft_harvest-bonares.py
```

This first executes a query to retrieve all dataset IDs from Bonares (using it's SOLR API). Then, for every dataset ID, the ISO 19139 compliant XML metadata is retrieved (which for some datasets contain metadata elements according to the Bonares specific schema extension [doi:10.1016/j.cageo.2019.07.005](https://doi.org/10.1016/j.cageo.2019.07.005)) and some of the metadata fields are transformed to schema.org compliant json-ld according to the RO-Crate profile.

The data is stored in a local file `results.json`.

4. Analyze the data.

In a local Python shell, run the following code in order to load the json-ld metadata and query which custom metadata properties are used the most.

```python
from rdflib import Graph
g = Graph()
g.parse("result0-2000.json")
g.parse("result2000-3903.json")

query = """
PREFIX schema: <http://schema.org/>

SELECT ?propName (COUNT(?propName) as ?count) {
    ?x a schema:Dataset .
    ?x schema:about ?y .
    ?y schema:object ?z .
    ?z schema:additionalProperty ?prop .
    ?prop schema:name ?propName .
}
GROUP BY ?propName
ORDER BY ?count
"""

sparql_result = g.query(query).bindings
print(f"Found {len(sparql_result)} unique property names")
for x in sparql_result:
    prop_name, count = x.values()
    print(f"{prop_name.value}: {count.value}")
```

This should print to the stdout something like e.g.:

```
[...]
Soil water content: 69
SHAPE: 70
Year: 70
Name: 74
Plot: 84
Parzelle_ID: 86
Versuchsjahr: 87
Site: 88
Date: 95
Treatment: 96
OBJECTID: 103
Bemerkungen_ID: 105
```

## NOTES
This was an experimental script to test out the capabilities of transforming Bonares metadata into RO-Crate-like JSON metadata and to investigate which domain-specific metadata properties are often used. Note that the metadata crosswalk applied on the ISO GMD xml metadata is far from complete. This work was done during the Biohackathon EU 2024.