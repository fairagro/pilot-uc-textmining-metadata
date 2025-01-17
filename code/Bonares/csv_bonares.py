import requests
import csv
import json

# URL to fetch data
url = "https://maps.bonares.de/finder/core0/select?q=*&wt=json&fl=id,type,title,accessConstraints,abstractType_de,description,publisherInfoForCatalog,resourceLanguage,available,spatial,subject&start=0&rows=5000"

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Extract the relevant records (assuming they are under the 'response' > 'docs' hierarchy)
    records = data.get("response", {}).get("docs", [])

    # Define the CSV file name
    csv_file_name = "/Users/husain/pilot-uc-textmining-metadata/data/Bonares/output/output_new.csv"

    # Define the CSV headers
    headers = [
        "ID", "title", "abstract_text",
        "keywords", "publication_year", "institute",
        "language","open_access"
    ]

    # Write the data to the CSV file
    with open(csv_file_name, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)

        # Write the header row
        writer.writeheader()

        # Write each record to the CSV
        for record in records:
            # Process accessConstraints
            ID = record.get("id",[])
            
            language = record.get("resourceLanguage", [])
            if language == "ger":
                language = "German"
            elif language == "eng":
                language = "English"
            elif language == "fra":
                language = "French"
            access_constraints = record.get("accessConstraints", [])
            if access_constraints == ["Es gelten keine Zugriffsbeschränkungen"]:
                record["open_access"] = True
            else:
                record["open_access"] = False

            # Extract year from available
            available = record.get("available", [])
            publication_year = ""
            if available and isinstance(available, list) and available[0]:
                publication_year = available[0].split("-")[0] if "-" in available[0] else available[0]
                if publication_year.isdigit():  # Ensure the year string is numeric
                    publication_year = int(publication_year)

            # Extract text from lists for specific fields
            abstract_text = ", ".join(record.get("description", [])) if isinstance(record.get("description"), list) else record.get("description", "")
            institute = ", ".join(record.get("publisherInfoForCatalog", [])) if isinstance(record.get("publisherInfoForCatalog"), list) else record.get("publisherInfoForCatalog", "")
            keywords = ", ".join(record.get("subject", [])) if isinstance(record.get("subject"), list) else record.get("subject", "")

            # Write only the fields in the headers
            writer.writerow({
                **{header: record.get(header, "") for header in headers if header not in ["ID","publication_year", "abstract_text", "institute", "keywords", "language"]},
                "publication_year": publication_year,
                "abstract_text": abstract_text,
                "institute": institute,
                "keywords": keywords,
                "ID": ID,
                "language": language
            })

    print(f"Data has been successfully written to {csv_file_name}")
else:
    print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
