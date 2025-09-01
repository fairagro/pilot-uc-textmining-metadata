FROM ubuntu:latest
LABEL authors="abdelmalak"

ENTRYPOINT ["top", "-b"]
# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app
COPY requirements.txt . 
# Install dependencies
RUN pip install -r requirements.txt 
RUN mkdir /output
RUN mkdir /data
# Copy the location related lists
COPY data_lists/countries_list.json data_lists/de_cities_list.json data_lists/de_regions_list.json /data/
# Copy scripts and requirements
COPY cas_folders_processing.py cas_to_csv_sentence.py cas_to_tokens.py create_data_from_inception.py viz_funcs.py .



# Set environment variables
ENV PARENT_FOLDER="/data/curation"
ENV PARENT_FOLDER_LEO="/data/annotation"
ENV CITY_LIST_PATH="/data/de_cities_list.json"
ENV REGION_LIST_PATH="/data/de_regions_list.json"
ENV COUNTRY_LIST_PATH="/data/countries_list.json"
ENV SAVE_CSV="/output/sentences_corpus.csv"
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "python create_data_from_inception.py \
  --parent_folder \"$PARENT_FOLDER\" \
  --parent_folder_leo \"$PARENT_FOLDER_LEO\" \
  --city_list_path \"$CITY_LIST_PATH\" \
  --region_list_path \"$REGION_LIST_PATH\" \
  --country_list_path \"$COUNTRY_LIST_PATH\" \
  --save_csv \"$SAVE_CSV\""]