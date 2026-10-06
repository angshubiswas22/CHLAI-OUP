import pandas as pd
import re
import os


INPUT_CSV = ""
OUTPUT_CSV = ""
TARGET_COLUMN = ""


def remove_parentheses_notes(text):
    if not isinstance(text, str) or not text.strip():
        return text
    

    cleaned = re.sub(r'\(.*?\)', '', text, flags=re.DOTALL)
    

    cleaned = re.sub(r' {2,}', ' ', cleaned)
    

    return cleaned.strip()

def run_stage4():
    print("Starting Stage 4: Parenthetical Note Removal...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Could not find '{INPUT_CSV}'. Please check the filename.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from {INPUT_CSV}.")
    
    if TARGET_COLUMN not in df.columns:
        print(f"Error: Column '{TARGET_COLUMN}' not found in the CSV.")
        return
        
    print(f"Scrubbing AI notes inside parentheses from '{TARGET_COLUMN}'...")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].apply(remove_parentheses_notes)
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Cleaned dataset saved to: '{OUTPUT_CSV}'")

if __name__ == "__main__":
    run_stage4()