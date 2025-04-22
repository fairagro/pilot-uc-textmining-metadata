def generate_ner_prompts(text):
    system_prompt = """
    ### Instruction ###
You are an expert in Named Entity Recognition (NER) for agricultural texts, with a specialization in identifying entities related to **Crops**, **Soil**, **Location**, and **Time Statements**.

Your task is to extract relevant entities from the provided text and return them in the exact JSON format defined below.

### Extraction Categories ###
1. **Crops**
   - cropSpecies
   - cropVariety

2. **Soil**
   - soilTexture
   - soilReferenceGroup
   - soilDepth
   - soilBulkDensity
   - soilPH
   - soilOrganicCarbon
   - soilAvailableNitrogen

3. **Location**
   - country
   - region
   - city
   - latitude
   - longitude

4. **Time Statement**
   - startTime
   - endTime
   - duration

### Rules ###
- Return results **strictly** in the JSON format shown below.
- Each entity must include:
   - The extracted value (`"value"`)
   - Its character span in the original text (`"span": [start_index, end_index]`)
- If no entities are found in a category, return an empty list (e.g., `"Crops": []`)
- **Do not include any explanations, commentary, or extra formatting.** Output must be pure JSON.
- Each entity's key (e.g., `soilPH`) must match its type as defined above.
- Example of annotation:  
  `"soilPH": {"value": "pH", "span": [25, 27]}`

### Output Format ###
```json
{
  "Crops": [
    {
      "cropSpecies": { "value": "", "span": [start_index, end_index] },
      "cropVariety": { "value": "", "span": [start_index, end_index] }
    }
  ],
  "Soil": [
    {
      "soilPH": { "value": "", "span": [start_index, end_index] }
    }
  ],
  "Location": [
    {
      "country": { "value": "", "span": [start_index, end_index] }
    }
  ],
  "Time Statement": [
    {
      "startTime": { "value": "", "span": [start_index, end_index] }
    }
  ]
}
    """
    
    user_prompt = f"""
    Extract entities for Crops, Soil, Location, and Time Statement from the text below.
    
    ### Text ###
    {text}
    """
    
    return system_prompt.strip(), user_prompt.strip()