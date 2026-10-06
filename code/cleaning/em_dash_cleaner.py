import os
import re
import pandas as pd

def clean_em_dashes(text):
    """
    Cleans em dashes (—) and double-hyphen equivalents (--).
    - Removes them completely if they are at the end of a line.
    - Replaces them with a single space if they are between words.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    
    # STAGE 1: Remove from the end of the line
    # Matches an em dash (or double hyphen), any optional trailing spaces, 
    # and the end of the line ($). The MULTILINE flag applies this line-by-line.
    cleaned = re.sub(r'(?:—|--)+\s*$', '', text, flags=re.MULTILINE)
    
    # STAGE 2: Replace remaining between words
    # Any em dash or double hyphen that survived Stage 1 is safely swapped for a space.
    cleaned = re.sub(r'(?:—|--)+', ' ', cleaned)
    
    # STAGE 3: Cleanup double spaces
    # If replacing the dash created an awkward double space between words, this fixes it.
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    return cleaned

def process_pipeline_csv(input_filepath="cleaned_poems_batch_stage1.csv", output_filepath="cleaned_poems_batch_stage2.csv"):
    """
    Loads the Stage 1 CSV file, applies the em-dash cleaning to the 
    'generated_poem' column, and outputs a pristine Stage 2 CSV file
    preserving all original columns and formatting structures.
    """
    # Safeguard check to ensure file exists
    if not os.path.exists(input_filepath):
        print(f"Error: The input file '{input_filepath}' was not found in this directory.")
        print("Please verify the file name or run your prior processing stage first.")
        return

    print(f"Loading pipeline dataset: '{input_filepath}'...")
    df = pd.read_csv(input_filepath)

    # Safeguard check to ensure the target column exists
    if "generated_poem" not in df.columns:
        print(f"Error: The column 'generated_poem' does not exist in '{input_filepath}'.")
        print(f"Found columns: {list(df.columns)}")
        return

    print(f"Running 2-stage cleaning logic across {len(df)} rows...")
    # Apply the solid cleaning logic strictly to the target column
    df['generated_poem'] = df['generated_poem'].apply(clean_em_dashes)

    print(f"Saving pristine dataset to: '{output_filepath}'...")
    # index=False ensures pandas doesn't write an accidental numeric row-id column
    df.to_csv(output_filepath, index=False)
    
    print("Success! Stage 2 processing is complete. All column headers remain identical.")

if __name__ == "__main__":
    process_pipeline_csv()