# Codebase Directory

This directory includes all the software developped for the pilot use case. As the use case is divided into different phases, each 
component is ran separately in its phase and each component is described as follows:

---

## Directory Structure
Each directory is for a specific task/RDI \
We have the following:\
* [utils](utils): Includes utility functions.
* [OpenAgrar](OpenAgrar): Includes code to download, manipulate and save metadata from OpenAgrar RDI.
* [Bonares](Bonares): Includes code to download, manipulate and save metadata from OpenAgrar RDI.
* [Pre-annotations](Pre-annoatations): This includes the pre-annotations and processing pipeline for the data downloaded from the resources.
* [corpus_creation](corpus_creation): This includes the pipelines to generate the final csv and JSON files of the annotated corpus in train and test splits.
* [Generate_annotations](Generate_annotations): This one includes a pilot code to use a trained model to generate annotations.


## Use Instructions 
Based on the task or the pipeline you would like to use, please refer to the directory containing this component. 