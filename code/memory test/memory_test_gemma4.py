import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import re


load_dotenv()


key = os.environ.get("OPENROUTER_API_KEY")
if not key:
    print("CRITICAL ERROR: I cannot find the OpenRouter key. Check your .env file!")
    exit()
else:
    print("Key loaded successfully! Connecting to OpenRouter...")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=key,
)

def clean_text(text):
    """Removes punctuation and lowercase text for a fair, strict comparison."""
    if pd.isna(text):
        return ""
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def test_gemma_memory():
    input_csv = ""
    output_csv = "Memory_test_output.csv"
    
    print(f"Loading {input_csv} for Gemma 4 testing...\n")
    
    try:
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip() 
    except FileNotFoundError:
        print(f"Error: Could not find '{input_csv}'.")
        return

    df['Gemma_Response'] = ""
    df['Memory_Match'] = False

    print("Starting the Memory Test with Gemma 4 31B (Free) via OpenRouter...\n")

    for index, row in df.iterrows():
        author = row['Author_Name']
        book = row['Book_Title']
        poem = row['Poem_Title']
        current_line = row['Current_Line']
        expected_next_line = row['Next_Line']

        book_context = ""
        if pd.notna(book) and str(book).strip().upper() != "NA":
            book_context = f"Book Title: {book}\n"
        system_prompt = "You are a highly precise text retrieval system. Output strictly the requested text and nothing else. No apologies, no quotes, no conversational filler."
        
        user_prompt = (
            f"Author Name: {author}\n"
            f"{book_context}"
            f"Poem Title: {poem}\n"
            f"Current Line: \"{current_line}\"\n\n"
            f"Please provide the exact next line of this poem."
        )

        try:

            response = client.chat.completions.create(
                model="google/gemma-4-31b-it:nitro", 
                temperature=0.0,                    
                max_tokens=50,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            message_obj = response.choices[0].message
            raw_content = getattr(message_obj, 'content', None)

            if raw_content:
                gemma_answer = raw_content.strip()
            else:
                gemma_answer = "ERROR: Empty response or content filter refusal"
                
            df.at[index, 'Gemma_Response'] = gemma_answer

 
            clean_expected = clean_text(expected_next_line)
            clean_gemma = clean_text(gemma_answer)

            if clean_expected and (clean_expected in clean_gemma or clean_gemma in clean_expected):
                df.at[index, 'Memory_Match'] = True
                match_status = "[MEMORIZED] Discard Author"
            else:
                df.at[index, 'Memory_Match'] = False
                match_status = "[CLEAN] Keep Author"

            print(f"Testing: {author} - '{poem}'")
            print(f"Expected: {expected_next_line}")
            print(f"Gemma:    {gemma_answer}")
            print(f"Result:   {match_status}\n")
            print("-" * 40 + "\n")


            time.sleep(15)

        except Exception as e:
            print(f"Error testing {author}: {e}\n")
            print("Hitting Google's rate limit. Pausing for 60 seconds to let the server cool down...")
            time.sleep(60)


    df.to_csv(output_csv, index=False)
    print(f"Results successfully saved to '{output_csv}'")


if __name__ == "__main__":
    test_gemma_memory()