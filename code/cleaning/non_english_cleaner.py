import pandas as pd
import re
import os


INPUT_CSV = ""
TXT_FILE = ""
OUTPUT_CSV = ""


def extract_row_numbers(txt_filepath):
    row_numbers = []
    if not os.path.exists(txt_filepath):
        print(f"[ERROR] Text file '{txt_filepath}' not found.")
        return row_numbers

    with open(txt_filepath, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r'Row\s+(\d+)', line)
            if match:
                row_numbers.append(int(match.group(1)))
    
    return sorted(list(set(row_numbers)))

def run_stage7():
    print("[INFO] Starting Stage 7: Dropping Non-English / Emoji Flagged Rows...")

    rows_to_drop = extract_row_numbers(TXT_FILE)
    if not rows_to_drop:
        print("[ERROR] No row numbers could be extracted from the text file. Aborting.")
        return
        
    print(f"[INFO] Successfully parsed text file. Found {len(rows_to_drop)} distinct rows targeted for removal.")

    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] Could not find '{INPUT_CSV}'. Please check the filename.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    original_row_count = len(df)
    print(f"[INFO] Loaded {original_row_count} rows from {INPUT_CSV}.")

    df_cleaned = df[~((df.index + 2).isin(rows_to_drop))]
    
    actual_dropped_count = original_row_count - len(df_cleaned)
 
    df_cleaned.to_csv(OUTPUT_CSV, index=False)
    
    print(f"[INFO] Verification: Expected to drop {len(rows_to_drop)} rows. Actually dropped {actual_dropped_count} rows.")
    print(f"Clean dataset saved to: '{OUTPUT_CSV}'")

if __name__ == "__main__":
    run_stage7()