import re
import os
import pandas as pd

# ==========================================
# CONFIGURATION
# ==========================================
RAW_INPUT_FILE = "generated_poems_batch.csv"
CLEAN_OUTPUT_FILE = "cleaned_poems_batch_stage1.csv"
COL_POEM = "generated_poem"
# ==========================================

def clean_raw_poem(text):
    if not isinstance(text, str) or not text.strip():
        return ""
    
    cleaned = text.strip()
    
    # -------------------------------------------------------------
    # STAGE 1: Strip Thought Blocks (Robust Fix)
    # -------------------------------------------------------------
    # Matches <think> and everything inside it.
    # The (?:</think>|$) ensures it still deletes the block even if the 
    # model hits its token limit and fails to generate the closing tag!
    cleaned = re.sub(r'<think>.*?(?:</think>|$)', '', cleaned, flags=re.DOTALL)
    
    # -------------------------------------------------------------
    # STAGE 2: Strip Markdown Fences
    # -------------------------------------------------------------
    cleaned = re.sub(r'```[a-zA-Z]*\n?', '', cleaned)
    cleaned = re.sub(r'```', '', cleaned)
    
    # -------------------------------------------------------------
    # STAGE 3: Strip Conversational Preamble & Labels
    # -------------------------------------------------------------
    cleaned = re.sub(r'^(Sure|Here is|This is a poem).*?:\s*\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\s*(?:\*{1,2}|#+)?\s*Title\s*(?:\*{1,2})?\s*:\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'^\s*(?:\*{1,2}|#+)?\s*Theme\s*(?:\*{1,2})?\s*:\s*.*?\n', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # -------------------------------------------------------------
    # STAGE 4: Em Dash Handling
    # -------------------------------------------------------------
    # 4.1 Strip em dashes from the end of lines
    cleaned = re.sub(r'(?:—|--)+\s*$', '', cleaned, flags=re.MULTILINE)
    # 4.2 Replace remaining em dashes between words with a space
    cleaned = re.sub(r'(?:—|--)+', ' ', cleaned)

    # -------------------------------------------------------------
    # STAGE 5: Mathematical, Relational & Special Symbol Scrubbing
    # -------------------------------------------------------------
    # Removes math operators and brackets (leaves round parentheses intact)
    cleaned = re.sub(r'[+\*/=<>\%\^@#\$\&~|\\\{\}\[\]_]', '', cleaned)
    
    # -------------------------------------------------------------
    # STAGE 6: Whitespace and Line Break Standardization
    # -------------------------------------------------------------
    cleaned = cleaned.strip()
    # Normalize double spaces that might be left behind after stripping symbols/dashes
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    # Normalize excessive carriage returns
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned

def run_cleaning_pipeline():
    print("Starting Downstream Cleaning Pipeline...")
    
    if not os.path.exists(RAW_INPUT_FILE):
        print(f"Error: Raw batch file '{RAW_INPUT_FILE}' not found. Cannot clean.")
        return
        
    try:
        df = pd.read_csv(RAW_INPUT_FILE, keep_default_na=False)
        print(f" Loaded raw dataset containing {len(df)} records.")
        
        if COL_POEM not in df.columns:
            print(f" Error: Column '{COL_POEM}' not found in the CSV. Available: {list(df.columns)}")
            return
            
        print("Processing text conversions and filtering special symbols...")
        df[COL_POEM] = df[COL_POEM].apply(clean_raw_poem)
        
        df.to_csv(CLEAN_OUTPUT_FILE, index=False)
        print(f"Cleaning complete! Exported clean dataset to: '{CLEAN_OUTPUT_FILE}'")
        
    except Exception as e:
        print(f"Script crashed during cleaning: {e}")

if __name__ == "__main__":
    run_cleaning_pipeline()