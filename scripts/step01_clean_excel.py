import pandas as pd
import os
import argparse
import re
import numpy as np
import csv
import json


# scripts/01_clean_excel.py

# === Config ===

# EXCEL_PATH = "excels/LKCHM Textual Inputs (ISS Masters Capstone).xlsx"
OUTPUT_CSV = "../excels/species_original_links.csv"


def clean_excel(path=None):
    if path.endswith(".xlsx"):
        excel_df = pd.read_excel(path)
    else:
        excel_df = pd.read_csv(path)

    # Extract species and lkc_content columns
    excel_df = excel_df.iloc[3:, 4:6].reset_index(drop=True)
    excel_df.columns = ['species', 'lkc_content']

    # Extract all URLs from lkc_content
    excel_df['url'] = excel_df['lkc_content'].apply(
        lambda text: re.findall(r'https?://[^\s\)\]\>\"\']+', str(text))
    )

    # Replace empty lists with NaN
    excel_df['url'] = excel_df['url'].apply(lambda x: np.nan if not x else json.dumps(x, ensure_ascii=False))  # ✅ JSON-stringify with double quotes
    excel_df.sort_values(by=['species'], inplace=True)
    return excel_df


def save_cleaned_links(df, output_csv=OUTPUT_CSV):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL)  # ✅ Enforce double-quoted CSV
    print(f"[✓] Saved cleaned species data to: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, help="Input your source file")
    args = parser.parse_args()
    EXCEL_PATH = args.source

    df_cleaned = clean_excel(EXCEL_PATH)
    save_cleaned_links(df_cleaned)