import asyncio
import re
from crawl4ai import *
import pandas as pd
import json
import os
from slugify import slugify
from urllib.parse import urlparse

# === Config ===
INPUT_CSV = "../excels/combined_links_v2_final.csv"
OUTPUT_DIR = "../data"


# def sanitize_filename(text):
#     return re.sub(r'[^a-zA-Z0-9_\-]', '_', text)[:80]  # avoid overly long names



def get_markdown_filename(species, url):
    domain = urlparse(url).netloc.split('.')[-2]
    return f"{species}_{domain}.md"


## Remove images from markdowns
def remove_images_from_markdown(markdown_text):
    # Remove image markdown ![alt text](url)
    cleaned = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_text)
    return cleaned.strip()


# def strip_links_keep_text(markdown_text):
#     """
#     Replaces [text](url) with just 'text'
#     """
#     return re.sub(r'\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)', r'\1', markdown_text)


def strip_links_keep_text(markdown: str) -> str:
    # Match [text](url "optional title")
    return re.sub(r'\[([^\]]+)\]\((https?:\/\/[^\s\)]+)(\s+"[^"]*")?\)', r'\1', markdown)


def already_scraped(species_folder):
    if not os.path.exists(species_folder):
        return set()
    return set(os.listdir(species_folder))


async def scrape_species_page(species_name, urls):
    species_dir = os.path.join(OUTPUT_DIR, species_name)
    os.makedirs(species_dir, exist_ok=True)
    existing_files = already_scraped(species_dir)

    async with AsyncWebCrawler() as crawler:
        for idx, url in enumerate(urls):
            # file_prefix = f"{idx+1:03d}"
            filename = get_markdown_filename(species_name, url)
            print(filename)
            # filename = f"{file_prefix}_{sanitize_filename(url)}.md"
            filepath = os.path.join(species_dir, filename)

            if filename in existing_files:
                print(f"[↪] Skipping {filename} — already exists.")
                continue

            try:
                result = await crawler.arun(url=url)
                cleaned_md = remove_images_from_markdown(result.markdown)
                cleaned_md = strip_links_keep_text(cleaned_md)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(cleaned_md)

                print(f"[✓] Saved: {filepath}")
            except Exception as e:
                print(f"[!] Failed to scrape {url} ({species_name}): {e}")


async def main():
    df = pd.read_csv(INPUT_CSV)
    df['url'] = df['url'].apply(json.loads)

    for _, row in df.iterrows():
        species_name = row['species']
        urls = row['url']
        await scrape_species_page(species_name, urls)


if __name__ == "__main__":
    asyncio.run(main())


# async def main():
#     async with AsyncWebCrawler() as crawler:
#         result = await crawler.arun(
#             url="https://www.nparks.gov.sg/avs/animals/wildlife-in-singapore/asian-koels",
#         )
        
#         cleaned_markdown = remove_images_from_markdown(result.markdown)
#         cleaned_markdown = strip_links_keep_text(cleaned_markdown)
#         print(cleaned_markdown)

# if __name__ == "__main__":
#     asyncio.run(main())
