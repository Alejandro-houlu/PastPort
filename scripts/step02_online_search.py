import pandas as pd
import requests
import time
import os
import argparse
import json
import ast


# === Config ===
# INPUT_CSV = "../excels/species_original_links.csv"
OUTPUT_CSV = "../excels/combined_links_v2.csv"
API_KEY = 'AIzaSyABc45FmUjsnXyyptXLKYEQgV0ryKwaeRE' #Google Custom API key
CX = 'a5b6d8c5546c642bc'  #https://programmablesearchengine.google.com/controlpanel/overview? Search Engine ID
NUM_RESULTS = 10


# === Helpers ===

# Parse 'url' column from string to list
def safe_parse(x):
    try:
        return ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) else None
    except Exception as e:
        print(f"[!] Could not parse URL list: {x} — {e}")
        return []


def load_existing_species():
    """
    Load species already processed (so we can skip them).
    """
    if not os.path.exists(OUTPUT_CSV):
        return set()

    df = pd.read_csv(OUTPUT_CSV)
    return set(df['species'].dropna())



## Google Search Species for URL
def google_url_search(query, api_key, cx, num_results=NUM_RESULTS):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': query,
        'key': api_key,
        'cx': cx,
        'num': num_results
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Google API Error: {response.status_code} — {response.text}")

    items = response.json().get("items", [])
    return [item['link'] for item in items]



def append_to_csv(species_name, url_list):
    try:
        url_json = json.dumps(url_list, ensure_ascii=False)  # ✅ JSON-safe format
    except Exception as e:
        print(f"[!] Failed to serialize URLs for {species_name}: {e}")
        return

    df_new = pd.DataFrame([{
        "species": species_name,
        "url": url_json  # ✅ Store as JSON string
    }])

    header = not os.path.exists(OUTPUT_CSV)
    df_new.to_csv(OUTPUT_CSV, mode='a', index=False, header=header)
    print(f"[✓] Saved {species_name} — {len(url_list)} URLs")



# === Main ===

def main(csv=None):
    df = pd.read_csv(csv)
    processed_species = load_existing_species()

    for _, row in df.iterrows():
        species_name = row['species']
        existing_url = ast.literal_eval(row['url']) if pd.notna(row['url']) and isinstance(row['url'], str) else None
        # existing_url = row['url'] if pd.notna(row['url']) else None

        if species_name in processed_species:
            print(f"[↪] Skipping {species_name} — already processed.")
            continue

        try:
            search_results = google_url_search(species_name.replace("_", " "), API_KEY, CX)
        except Exception as e:
            print(f"[!] Error for {species_name}: {e}")
            print("[!] Save progress and resume later.")
            break  # Stop so you can resume the next day without reprocessing
        time.sleep(1)  # Be nice to API

        if existing_url:
            combined = set(search_results + existing_url)
        else:
            combined = set(search_results)

        append_to_csv(species_name, list(combined))

    df_final = pd.read_csv(OUTPUT_CSV)
    df_final = df_final.sort_values(by=["species"]).reset_index(drop=True)
    df_final.to_csv(OUTPUT_CSV, index=False)
    print(f"[✓] Saved cleaned species data to: {OUTPUT_CSV}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputcsv', type=str, help="Input your original url file")
    args = parser.parse_args()  
    INPUT_CSV = args.inputcsv
    main(INPUT_CSV)