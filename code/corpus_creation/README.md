## This directory includes the code to convert the inception projects into the corpus files 
### Prerequisites

Make sure you have Docker installed. For installation instructions, visit [Docker's official documentation](https://docs.docker.com/get-docker/).

---

### Build the Docker Image
```bash
docker build -t create_corpus_from_inception .
docker run   -v "$(pwd)":/dataset_files   -v /home/abdelmalak/Documents/FAIRagro/webanno17101708295286074066export_curated_documents/curation:/data/curation   -v /home/abdelmalak/Documents/FAIRagro/admin-58560539323484181674/annotation:/data/annotation   -v /home/abdelmalak/Documents/FAIRagro:/data/lists   create_corpus_from_inception
```
Feel free to replace the `$(pwd)` with the directory where you want to save the data

Replace the `/home/abdelmalak/Documents/FAIRagro/webanno17101708295286074066export_curated_documents/curation` with the curation project

Replace the `/home/abdelmalak/Documents/FAIRagro/admin-58560539323484181674/annotation` with the other annotation project

`/home/abdelmalak/Documents/FAIRagro` this is the directory to the location curation lists

### The output
It should outpust 4 csv files in total 

They should be as follows

* File-based corpus
    * Train_file_corpus.csv
    * Test_file_corpus.csv
* Sentence-base corpus
    * Train_sentence_corpus.csv
    * Test_file_corpus.csv

