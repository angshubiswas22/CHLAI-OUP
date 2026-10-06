import pandas as pd

def remove_empty_rows(csv_filename, column_name, output_filename):
    # Read the CSV file
    df = pd.read_csv(csv_filename)
    
    # Check if the column exists to avoid errors
    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in the CSV.")
        return
    
    # 1. Identify which rows have missing values in the target column
    # Adding 2 converts the 0-based Pandas index to 1-based CSV/Excel row numbers
    dropped_rows = (df[df[column_name].isna()].index + 2).tolist()
    
    # 2. Drop rows where the target column is null
    df_cleaned = df.dropna(subset=[column_name])
    
    # 3. Save the cleaned dataframe to a new CSV file
    df_cleaned.to_csv(output_filename, index=False)
    
    # 4. Print results
    print(f"Successfully processed the file.")
    if dropped_rows:
        print(f"Removed {len(dropped_rows)} row(s) that had empty values in '{column_name}'.")
        print(f"Dropped row numbers (matching Excel/CSV): {dropped_rows}")
    else:
        print(f"No empty cells found in column '{column_name}'. No rows were dropped.")
        
    print(f"Cleaned data saved to: {output_filename}")

# --- Usage ---
# Ensure 'data.csv' is in the same folder as this script
remove_empty_rows(
    csv_filename='cleaned_poems_batch_stage2.csv', 
    column_name='generated_poem',
    output_filename='cleaned_poems_batch_stage3.csv'
)