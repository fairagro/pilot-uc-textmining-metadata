from rdflib import Graph
import json
import argparse

def load_ttl_file(filepath):
    g = Graph()
    g.parse(filepath, format="ttl")  # "ttl" = Turtle format
    print(f"Loaded {len(g)} triples from {filepath}")
    list = []
    # Print the first few triples
    for i, (s, p, o) in enumerate(g):
        #print(s)
        # print(f"{s} {p} {o}")
        if str(p).startswith("http://www.w3.org/2000/01/rdf-schema#label") and str(s).split("#")[-1].startswith("KA"):
            if str(s).endswith("SoilTexture"):
                continue
            else:
                list.append(str(o))
    return list

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Compare or process two JSON files.")
    parser.add_argument(
        "--json1", type=str, default="/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/dataset_files/ConceptsList/soilTexture_list.json",
        help="Path to the first JSON file (default: default1.json)"
    )
    parser.add_argument(
        "--json2", type=str, default="/home/abdelmalak/Documents/FAIRagro/SoilTexture.ttl",
        help="Path to the second JSON file (default: default2.json)"
    )
    args = parser.parse_args()
    graph = load_ttl_file(args.json2)

    data = load_json(args.json1)
    #print(data)
    data.extend(graph)
    #print(graph)
    print(data)
    with open(args.json1, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()

    
