import pandas as pd
import re
import os

INPUT_CSV = ""
OUTPUT_CSV = ""
TARGET_COLUMN = ""

def clean_ellipses(text):
    if not isinstance(text, str) or not text.strip():
        return text

    cleaned = re.sub(r'(?:…|\.{3,})+\s*$', '', text, flags=re.MULTILINE)
    
    cleaned = re.sub(r'(?:…|\.{3,})+', ' ', cleaned)
    
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    return cleaned.strip()

def run_stage6():
    print("[INFO] Starting Stage 6: Ellipsis Cleanup Pipeline...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] Could not find '{INPUT_CSV}'. Please check the filename.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"[INFO] Loaded {len(df)} rows from {INPUT_CSV}.")
    
    if TARGET_COLUMN not in df.columns:
        print(f"[ERROR] Column '{TARGET_COLUMN}' not found in the CSV.")
        return
        
    print(f"[INFO] Scrubbing trailing and mid-sentence ellipses from '{TARGET_COLUMN}'...")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].apply(clean_ellipses)
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Cleaned file saved to: '{OUTPUT_CSV}'")

if __name__ == "__main__":
    run_stage6()