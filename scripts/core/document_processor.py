from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from config.settings import Config
import os

class DocumentProcessor:
    def __init__(self, chunk_size: int = Config.CHUNK_SIZE, 
                 chunk_overlap: int = Config.CHUNK_OVERLAP,
                 max_filename_length=20):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_filename_length = max_filename_length

    
    def load_chunks(self, root_folder: str = Config.DEFAULT_ROOT_FOLDER, 
                   species_folder_name: str = Config.DEFAULT_SPECIES_FOLDER):
        """Load and chunk documents - your existing function"""
        chunks = []

        root_path = Path(root_folder)
        
        print(f"🔍 Processing folder: {root_folder}/{species_folder_name}")
        
        for species_folder in root_path.iterdir():
            if not species_folder.is_dir():
                continue
            if species_folder.name != species_folder_name:
                continue

            for filepath in species_folder.glob("*"):
                if filepath.suffix == ".pdf":
                    filepath = filepath.resolve()
                    loader = PyPDFLoader(str(filepath))
                    raw_docs = loader.load()

                    for doc in raw_docs:
                        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                        pdf_chunks = splitter.split_documents([doc])

                        for idx, subchunk in enumerate(pdf_chunks):
                            subchunk.metadata["species"] = species_folder.name
                            subchunk.metadata["source"] = filepath.name.replace(f"{species_folder.name}_", "")[:self.max_filename_length]
                            subchunk.metadata["chunk_id"] = idx + 1
                            # PyPDFLoader usually includes 'page' in doc.metadata already
                            if "page" in doc.metadata:
                                subchunk.metadata["page"] = doc.metadata["page"] + 1

                            species_tag = subchunk.metadata.get('species')
                            source_tag = subchunk.metadata.get('source') 
                            page_tag = subchunk.metadata.get('page') 
                            chunk_id_tag = subchunk.metadata.get('chunk_id')
                            subchunk.metadata["doc_tag"] = f'{species_tag}:{source_tag}:{page_tag}:{chunk_id_tag}'

                        chunks.extend(pdf_chunks)

                elif filepath.suffix == ".md":
                    loader = TextLoader(str(filepath), encoding="utf-8")
                    raw_docs = loader.load()

                    for doc in raw_docs:
                        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
                            ("#", "title"),
                            ("##", "section"),
                            ("###", "subsection")
                        ])
                        md_chunks = splitter.split_text(doc.page_content)

                        for idx, subchunk in enumerate(md_chunks):
                            subchunk.metadata["species"] = species_folder.name
                            subchunk.metadata["source"] = filepath.name.replace(f"{species_folder.name}_", "")
                            subchunk.metadata["chunk_id"] = idx + 1
                            subchunk.metadata["page"] = 0

                            # If markdown section info is present, copy it
                            for field in ["title", "section", "subsection"]:
                                if field in subchunk.metadata:
                                    subchunk.metadata["section"] = subchunk.metadata[field]
                                    break  # Only use the most specific
                                    
                            species_tag = subchunk.metadata.get('species')        
                            source_tag = subchunk.metadata.get('source') 
                            page_tag = subchunk.metadata.get('page') 
                            chunk_id_tag = subchunk.metadata.get('chunk_id')
                            subchunk.metadata["doc_tag"] = f'{species_tag}:{source_tag}:{page_tag}:{chunk_id_tag}'
                            
                        chunks.extend(md_chunks)
                    # pass

                else:
                    print(f"[!] Skipping unsupported file type: {filepath}")

        print(f"\n[✓] Total chunks ready: {len(chunks)}")
        return chunks

    
    def get_chunk_ids(self, chunks):
        """Extract IDs from chunks"""
        return [chunk.metadata.get("doc_tag") for chunk in chunks]
