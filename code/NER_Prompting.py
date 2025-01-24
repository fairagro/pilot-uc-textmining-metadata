import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Step 1: Load LLaMA Model and Tokenizer
def load_llama_model(model_name="openlm-research/open_llama_7b"):
    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", torch_dtype=torch.float16
    )
    print("Model and tokenizer loaded.")
    return model, tokenizer

# Step 2: Define Prompt for NER
def create_ner_prompt(text):
    prompt = f"""
    Extract all named entities from the following text and categorize them into Person, Organization, Location, and Date:
    
    Text: "{text}"
    Provide the output in this format:
    - Person: [List of Persons]
    - Organization: [List of Organizations]
    - Location: [List of Locations]
    - Date: [List of Dates]
    """
    return prompt

# Step 3: Perform NER with LLaMA
def perform_ner_with_llama(model, tokenizer, text, max_length=512):
    # Create the NER prompt
    prompt = create_ner_prompt(text)
    
    # Tokenize the input
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length).to("cuda")
    
    # Generate output
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        top_p=0.9,
    )
    
    # Decode the output
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Step 4: Process Text Data from CSV
def process_csv(csv_path, model, tokenizer, output_csv_path="ner_results.csv"):
    print(f"Loading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)  # Load CSV file
    
    if "abstract_text_2" not in df.columns:
        raise ValueError("CSV must contain a column named 'text' with the text data.")
    
    # Apply NER to each row
    results = []
    for idx, text in enumerate(df["abstract_text_2"]):
        print(f"Processing row {idx + 1}/{len(df)}...")
        try:
            ner_result = perform_ner_with_llama(model, tokenizer, text)
            results.append(ner_result)
        except Exception as e:
            print(f"Error processing row {idx + 1}: {e}")
            results.append("Error")
    
    # Add results to the DataFrame
    df["ner_results"] = results
    
    # Save to a new CSV file
    df.to_csv(output_csv_path, index=False)
    print(f"NER results saved to {output_csv_path}")
    return df

# Step 5: Main Execution
if __name__ == "__main__":
    # Path to the input CSV file
    input_csv_path = "C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\output_new_data.csv"  # Replace with your CSV file path
    
    # Load the model
    llama_model, llama_tokenizer = load_llama_model("openlm-research/open_llama_7b")
    
    # Perform NER and save results
    output_csv_path = "C:\Users\husain\pilot-uc-textmining-metadata\data\Bonares\output\ner_results.csv"
    processed_df = process_csv(input_csv_path, llama_model, llama_tokenizer, output_csv_path)
    
    print("NER processing complete. Sample results:")
    print(processed_df.head())
