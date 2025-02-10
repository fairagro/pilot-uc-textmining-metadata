FROM ubuntu:latest
LABEL authors="abdelmalak"

ENTRYPOINT ["top", "-b"]
# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy scripts and requirements
COPY processing.py url_manipulation.py llist_harvester.py fetch_bonares.py excel_bonares.py requirements.txt .
COPY mappings/mapping-implementation/ .
# Install dependencies
RUN pip install -r requirements.txt
RUN mkdir /output
# Set environment variables
ENV BONARES_URL="https://maps.bonares.de/finder/core0/select?q=*&wt=json&fl=id,type&start=0&rows=5000"
ENV DATAJSONFILE="/output/output.json"
ENV DATACSVFILE="/output/output.csv"
ENV DATAEXCELFILE="/output/output.xlsx"
ENV PYTHONUNBUFFERED=1

# Run both scripts in sequence
#CMD python fetch_bonares.py && python excel_bonares.py
#CMD python excel_bonares.py
CMD  python excel_bonares.py