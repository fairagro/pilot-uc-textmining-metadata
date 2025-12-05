FROM ubuntu:latest
LABEL authors="abdelmalak"

ENTRYPOINT ["top", "-b"]
# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy scripts and requirements
COPY processing.py url_manipulation.py llist_harvester.py fetch_openagrar.py filter_openagrar.py requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt
RUN mkdir /dataset_files
# Set environment variables
ENV OPENAGRAR_URL="https://www.openagrar.de/servlets/OAIDataProvider?verb=ListRecords&metadataPrefix=oai_datacite&set=GENRE:research_data"
ENV DATAJSONFILE="/output/output.json"
ENV DATACSVFILE="/output/output.csv"
ENV PYTHONUNBUFFERED=1

# Run both scripts in sequence
CMD python fetch_openagrar.py && python filter_openagrar.py
#CMD python filter_openagrar.py