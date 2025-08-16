import pandas as pd
import ast
import argparse
import json

def main(species_csv, flatten_csv, output_csv):
    # Load both CSVs
    species_df = pd.read_csv(species_csv)
    flatten_df = pd.read_csv(flatten_csv)

    # Clean and standardize the 'keep' column
    flatten_df['keep (Y/N)'] = flatten_df['keep (Y/N)'].str.strip().str.upper()

    # Create a dict of links to remove for each species
    to_remove = (
        flatten_df[flatten_df['keep (Y/N)'] == 'N']
        .groupby('species')['url']
        .apply(set)
        .to_dict()
    )

    def filter_links(row):
        species = row['species']
        try:
            links = ast.literal_eval(row['url'])
        except Exception:
            return row['url']  # skip malformed rows

        if species in to_remove:
            links = [link for link in links if link not in to_remove[species]]
        return json.dumps(links)  # Use JSON format with double quotes

    # Apply filtering
    species_df['url'] = species_df.apply(filter_links, axis=1)
    species_df.sort_values(by=['species'], inplace=True)

    # Save result
    species_df.to_csv(output_csv, index=False)
    print(f"Filtered species saved to: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter species links based on flatten.csv markings")
    parser.add_argument("--speciescsv", type=str, required=True, help="Path to species CSV file")
    parser.add_argument("--flattencsv", type=str, required=True, help="Path to flattened CSV file")
    parser.add_argument("--outputcsv", type=str, default="species_filtered.csv", help="Output CSV file")

    args = parser.parse_args()
    main(args.speciescsv, args.flattencsv, args.outputcsv)
