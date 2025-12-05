import argparse
import json

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
        "--json1", type=str, default="/home/abdelmalak/Documents/FAIRagro/uc_repo/repo/pilot-uc-textmining-metadata/data/Bonares/dataset_files/ConceptsList/soilReferenceGroup.json",
        help="Path to the first JSON file (default: default1.json)"
    )
    parser.add_argument(
        "--json2", type=str, default="/home/abdelmalak/Documents/FAIRagro/uc_repo/WRBReferenceSoilGroupValue.de.json",
        help="Path to the second JSON file (default: default2.json)"
    )
    
    args = parser.parse_args()

    out_list = []
    isnpire_data = load_json(args.json2)
    for i in isnpire_data["codelist"]["containeditems"]:
        name = i["value"]["label"]["text"].lower()
        out_list.append(name)
        if name[-1] == "s":
            out_list.append(name[:-1])
        
    #print(out_list)
    with open(args.json1, "w", encoding="utf-8") as f:
        json.dump(out_list, f, ensure_ascii=False, indent=4)
if __name__ == "__main__":
    main()
