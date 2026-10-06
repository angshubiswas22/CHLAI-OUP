import os
import random
import csv
import time  
import pandas as pd
from dotenv import load_dotenv


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq


load_dotenv() 


API_KEY = os.getenv("GROQ_ORG2_API_KEY")

if not API_KEY:
    print("Error: Please make sure GROQ_ORG2_API_KEY is set in your .env file.")
    exit()

def load_human_data(filepath=""):
    try:
        df = pd.read_csv(filepath)
        df = df.fillna('')
        return df.to_dict('records')
    except Exception as e:
        print(f" Error loading CSV: {e}")
        exit()

HUMAN_DATA = load_human_data()
print(f" Loaded {len(HUMAN_DATA)} human poem entries.")

models = {
    "llama-3.3-70b": ChatGroq(temperature=0.8, model_name="llama-3.3-70b-versatile", groq_api_key=API_KEY),
    "gpt-oss-120b": ChatGroq(temperature=0.8, model_name="openai/gpt-oss-120b", groq_api_key=API_KEY),
    "qwen-3-32b": ChatGroq(temperature=0.7, model_name="qwen/qwen3-32b", groq_api_key=API_KEY) 
}
print(" Loaded Models for Organization 2: Llama 3.3, GPT-OSS, Qwen 3")


GLOBAL_THEMES = [
    "Love", "Romanticism", "Heartbreak", "Faith", "Nature", 
    "Grief", "Joy", "Mortality", "Nostalgia", "Desire", 
    "Betrayal", "Hope", "Melancholy", "Solitude", "Rebirth", 
    "Eternity", "Beauty", "Sorrow", "Wonder", "Resilience"
] 


UNIVERSAL_STYLE_INSTRUCTIONS = (
"STYLE GUIDE:\n"
    "1. TITLE: Provide a meaningful, original TITLE at the very top of the poem.\n"
    "2. CONSTRAINTS: Only English language poems are allowed. Do NOT use em dashes (—).\n"
    "3. ORIGINALITY: Do NOT plagiarize or directly copy the provided author's work. Absorb their stylistic voice, but generate a 100% original poem based on the given theme.\n"
)


def get_few_shot_block(author_name, n=2):
    """Picks random examples specifically for the target author."""
    author_samples = [s for s in HUMAN_DATA if s.get('Author') == author_name]
    
    n = min(n, len(author_samples))
    if n == 0: return "" 
    
    samples = random.sample(author_samples, n)
    
    block = (
        f"Here are {n} examples of {author_name}'s writing style. "
        "Use these ONLY to understand their voice, rhythm, and formatting. "
        "Do NOT copy the content. Write a completely new poem based on the assigned theme.\n"
    )
    
    for i, s in enumerate(samples):
        text = str(s.get('Poems', '')).strip()
        title=str(s.get('Title','')).strip()
        block += (
            f"\n--- EXAMPLE {i+1} ---\n"
            f"TITLE: {title}\n"
            f"POEM:\n{text}\n"
            f"--- END EXAMPLE ---\n"
        )
    return block


output_file = "generated_poems_batch.csv"
completed_jobs = set()
if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
    try:
        df_existing = pd.read_csv(output_file)
        if "entry_index" in df_existing.columns and "model" in df_existing.columns:
            for _, row in df_existing.iterrows():

                completed_jobs.add((int(row["entry_index"]), str(row["model"])))
        print(f" Found existing progress file. Skipping {len(completed_jobs)} already completed jobs.")
    except Exception as e:
        print(f" Could not read progress file, starting fresh: {e}")

job_list = []

for entry_index, entry in enumerate(HUMAN_DATA):
    author = entry.get('Author', 'Unknown')
    for model_name in models.keys():
        if (entry_index, model_name) in completed_jobs:
            continue
            
        job_list.append({
            "model": model_name,
            "author": author,
            "theme": random.choice(GLOBAL_THEMES), 
            "entry_index": entry_index 
        })

random.shuffle(job_list)
total_jobs = len(job_list)
print(f" Total remaining jobs to process on Organization 2: {total_jobs}")


RPM_LIMITS = {"llama-3.3-70b": 28, "gpt-oss-120b": 28, "qwen-3-32b": 58}
RPD_LIMITS = {"llama-3.3-70b": 990, "gpt-oss-120b": 990, "qwen-3-32b": 990}


TPM_LIMITS = {"llama-3.3-70b": 11500, "gpt-oss-120b": 7500, "qwen-3-32b": 5500}
TPD_LIMITS = {"llama-3.3-70b": 99000, "gpt-oss-120b": 199000, "qwen-3-32b": 499000}

request_history = {model: [] for model in models.keys()}
token_history = {model: [] for model in models.keys()}  

session_request_counts = {model: 0 for model in models.keys()}
session_token_counts = {model: 0 for model in models.keys()}
EXHAUSTED_MODELS = set()

def estimate_tokens(text):
    """Conservative token estimation based on character length."""
    return len(text) // 3

def enforce_rate_limit(model_name, current_prompt_text):
    """Ensures we don't exceed RPM, RPD, TPM, or TPD limits. Returns False if limit hit."""
    if model_name in EXHAUSTED_MODELS:
        return False

    current_time = time.time()
    est_prompt_tokens = estimate_tokens(current_prompt_text)
    est_total_tokens = est_prompt_tokens + 400  

    if session_request_counts[model_name] >= RPD_LIMITS[model_name]:
        print(f"    [Status] {model_name} hit daily request limit ({RPD_LIMITS[model_name]}). Marking as exhausted.")
        EXHAUSTED_MODELS.add(model_name)
        return False
        
    if session_token_counts[model_name] + est_total_tokens >= TPD_LIMITS[model_name]:
        print(f"    [Status] {model_name} approaching daily token limit ({session_token_counts[model_name]} used). Marking as exhausted.")
        EXHAUSTED_MODELS.add(model_name)
        return False

    # Clean up 60-second sliding windows
    while request_history[model_name] and current_time - request_history[model_name][0] > 60:
        request_history[model_name].pop(0)
        
    while token_history[model_name] and current_time - token_history[model_name][0][0] > 60:
        token_history[model_name].pop(0)

    current_window_tokens = sum(tokens for _, tokens in token_history[model_name])

    if len(request_history[model_name]) >= RPM_LIMITS[model_name] or (current_window_tokens + est_total_tokens) >= TPM_LIMITS[model_name]:
        oldest_req = request_history[model_name][0] if request_history[model_name] else current_time
        oldest_tok = token_history[model_name][0][0] if token_history[model_name] else current_time
        oldest_timestamp = min(oldest_req, oldest_tok)
        
        sleep_time = 60.0 - (current_time - oldest_timestamp)
        if sleep_time > 0:
            print(f"    [Rate Limit] {model_name} reaching minute bounds ({current_window_tokens} tokens/min active). Sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time + 1.0)
            
        current_time = time.time()
        while request_history[model_name] and current_time - request_history[model_name][0] > 60:
            request_history[model_name].pop(0)
            
        while token_history[model_name] and current_time - token_history[model_name][0][0] > 60:
            token_history[model_name].pop(0)

    request_history[model_name].append(time.time())
    session_request_counts[model_name] += 1
    return True

def update_token_usage(model_name, prompt_text, response_text):
    """Logs precise token consumption into trackers following successful generation."""
    actual_tokens = estimate_tokens(prompt_text + response_text)
    token_history[model_name].append((time.time(), actual_tokens))
    session_token_counts[model_name] += actual_tokens

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "CRITICAL DIRECTIVE: Your main task is poem generation. You are an expert creative poet mimicking a specific human style.\n\n{style_guide}"),
    ("human", "Generate a brand new, original poem based on the following theme.\nTHEME: {theme}")
])

output_file = "generated_poems_batch.csv"
csv_headers = ["model", "prompt_type", "author", "themes", "generated_poem", "picked", "entry_index"]

print(f"\n--- Generation Loop ({total_jobs} Remaining Poems) ---")

file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0

with open(output_file, 'a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=csv_headers)
    if not file_exists:
        writer.writeheader()
    
    for i, job in enumerate(job_list):
        model_name = job["model"]
        author = job["author"]
        theme = job["theme"]
        
        if model_name in EXHAUSTED_MODELS:
            if set(models.keys()).issubset(EXHAUSTED_MODELS):
                print("\nAll models on Organization 2 have reached their daily token/request buffers. Exiting pipeline.")
                break
            continue
            
        print(f"  > Job {i+1}/{total_jobs}: [{model_name}] [Few-Shot] Author: {author} | Theme: {theme}")
        
        style_guide = UNIVERSAL_STYLE_INSTRUCTIONS + "\n\n" + get_few_shot_block(author, n=2)
        full_prompt_string = style_guide + "\n" + theme
            
        llm = models[model_name]
        chain = prompt_template | llm | StrOutputParser()
        
        try:
            allowed = enforce_rate_limit(model_name, full_prompt_string)
            if not allowed:
                print(f"    Skipping job due to daily capacity boundaries.")
                continue
            
            raw_output = chain.invoke({
                "style_guide": style_guide,
                "theme": theme
            })
            
            update_token_usage(model_name, full_prompt_string, raw_output)
            
            writer.writerow({
                "model": model_name,
                "prompt_type": "few-shot",
                "author": author,
                "themes": theme,
                "generated_poem": raw_output,
                "picked": 0,
                "entry_index": job["entry_index"]
            })
            f.flush()  
            print(f"    Success!")
            
        except Exception as e:
            error_msg = str(e)
            print(f"    Error: {error_msg}")
            
            if "tokens per day (TPD)" in error_msg or "requests per day (RPD)" in error_msg:
                print(f"    [Server Sync] {model_name} hit remote daily limit. Marking as exhausted.")
                EXHAUSTED_MODELS.add(model_name)
            elif "503" in error_msg or "500" in error_msg or "Service Unavailable" in error_msg:
                print(f"    [Server Hiccup] Groq overloaded. Pausing script for 10 seconds...")
                time.sleep(10)

print(f"\n--- Generation Loop Cycle Finished. Output saved to {output_file} ---")