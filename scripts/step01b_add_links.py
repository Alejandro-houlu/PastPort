import pandas as pd
import json
import os
import argparse
import ast
import numpy as np

# === Helpers ===

def load_dataframe(path):
    df = pd.read_csv(path)

    # Normalize species names: lowercase, strip spaces, replace underscores
    df['species'] = df['species'].str.replace("_", " ").str.strip().str.lower()

    # Parse 'url' column from string to list
    def safe_parse(x):
        try:
            return ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) else []
        except Exception as e:
            print(f"[!] Could not parse URL list: {x} — {e}")
            return []

    df['url'] = df['url'].apply(safe_parse)
    
    return df

def update_links(existing_df, new_df):
    for _, row in new_df.iterrows():
        species = row['species']
        new_links = row['url']

        match = existing_df['species'] == species
        if match.any():
            existing_links = existing_df.loc[match, 'url'].values[0]
            combined = list(set(existing_links + new_links))  # deduplicate

            # Fix: update the single cell
            idx = existing_df.index[match][0]
            existing_df.at[idx, 'url'] = combined

            print(f"[↺] Updated links for: {species} ({len(new_links)} new, total: {len(combined)})")
        else:
            existing_df = pd.concat([existing_df, pd.DataFrame([{
                "species": species,
                "url": new_links
            }])], ignore_index=True)
            print(f"[+] Added new species: {species} ({len(new_links)} links)")
    
    existing_df['species'] = existing_df['species'].str.replace(" ", "_")
    existing_df['url'] = existing_df['url'].apply(lambda x: np.nan if not x else json.dumps(x, ensure_ascii=False))  # ✅ JSON-stringify with double quotes
    existing_df.sort_values(by=['species'], inplace=True)
    return existing_df


def save_dataframe(df, output_path):
    df.to_csv(output_path, index=False, quotechar='"')
    print(f"[✓] Saved updated links to: {output_path}")

# === Main ===

def main(BASE_CSV, NEW_LINKS_CSV, OUTPUT_CSV):
    if not os.path.exists(BASE_CSV):
        print(f"[!] File not found: {BASE_CSV}")
        return

    df_existing = load_dataframe(BASE_CSV)
    df_new = load_dataframe(NEW_LINKS_CSV)

    df_updated = update_links(df_existing, df_new)
    df_updated.to_csv(OUTPUT_CSV, index=False)
    print(f"[✓] Updated species links saved to test.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--basecsv', type=str, help="Input your base file to be updated")
    parser.add_argument('--newlinkscsv', type=str, help="Select your new links file")
    parser.add_argument('--outputcsv', type=str, help="Select your output path")
    args = parser.parse_args()  
    BASE_CSV = args.basecsv
    NEW_LINKS_CSV = args.newlinkscsv
    OUTPUT_CSV = args.outputcsv
    main(BASE_CSV, NEW_LINKS_CSV, OUTPUT_CSV)
