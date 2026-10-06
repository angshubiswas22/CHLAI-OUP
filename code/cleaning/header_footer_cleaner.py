import pandas as pd
import re
import os


INPUT_CSV = ""
OUTPUT_CSV = ""
TARGET_COLUMN = ""
# ==========================================

def clean_headers_and_footers(text):
    if not isinstance(text, str) or not text.strip():
        return text
    cleaned = re.sub(r'(?i)^\s*(?:\*\*|__)?POEM(?:\*\*|__)?\s*:\s*', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'(?i)^\s*[^\w\s]*\s*END POEM\s*[^\w\s]*\s*$', '', cleaned, flags=re.MULTILINE)
    
    
    return cleaned.strip()

def run_stage5():

    
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] Could not find '{INPUT_CSV}'. Please check the filename.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"[INFO] Loaded {len(df)} rows from {INPUT_CSV}.")
    
    if TARGET_COLUMN not in df.columns:
        print(f"[ERROR] Column '{TARGET_COLUMN}' not found in the CSV.")
        return
        
    print(f"[INFO] Scrubbing 'POEM:' headers, decorated 'END POEM' footers, and stray symbols...")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].apply(clean_headers_and_footers)
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Cleaned dataset saved to: '{OUTPUT_CSV}'")

if __name__ == "__main__":
    run_stage5()