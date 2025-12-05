## This directory includes the code to harvest and save data from OpenAgrar RDI
### Prerequisites

Make sure you have Docker installed. For installation instructions, visit [Docker's official documentation](https://docs.docker.com/get-docker/).

---

### Build the Docker Image
```bash
docker build -t openagrar_data .
docker run --rm -v "$(pwd)/../../data/OpenAgrar/outputs:/output" openagrar_data
```
Feel free to replace the `$(pwd)/../../data/OpenAgrar/outputs` with the directory where you want to save the data

--- 
## Generate the text files
After storing the csv data from OpenAgrar, run the following code to generate the text files
```bash
python export_text_files/csv_to_text.py --csv_file data/datasets.csv --out_dir output/textfiles
```