from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from config.settings import Config
import os
import re

class DocumentProcessor:
    def __init__(self, chunk_size: int = Config.CHUNK_SIZE, 
                 chunk_overlap: int = Config.CHUNK_OVERLAP,
                 max_filename_length=20):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_filename_length = max_filename_length

    
    def clean_text(self, text: str) -> str:
        """Remove excessive newlines and spaces."""
        text = re.sub(r'\s+', ' ', text)  # replace multiple whitespace/newlines with a single space
        return text.strip()

    
    def get_species_folders(self, root_folder: str, species_folder_names):
        """
        Get list of species folders to process based on input.
        
        Args:
            root_folder: Root directory path
            species_folder_names: Can be:
                - "all": process all folders
                - list of folder names: process specific folders
                - single string: process one folder
        
        Returns:
            List of folder names to process
        """
        root_path = Path(root_folder)
        
        if not root_path.exists():
            print(f"❌ Root folder does not exist: {root_folder}")
            return []
        
        # Get all available folders
        all_folders = [f.name for f in root_path.iterdir() if f.is_dir()]
        
        if not all_folders:
            print(f"❌ No folders found in: {root_folder}")
            return []
        
        # print(f"📁 Available folders: {all_folders}")
        
        # Handle different input types
        if isinstance(species_folder_names, str):
            if species_folder_names.lower() == "all":
                print(f"🌟 Processing ALL folders: {all_folders}")
                return all_folders
            else:
                # Single folder
                if species_folder_names in all_folders:
                    print(f"📂 Processing single folder: {species_folder_names}")
                    return [species_folder_names]
                else:
                    print(f"❌ Folder not found: {species_folder_names}")
                    return []
        
        elif isinstance(species_folder_names, list):
            # Multiple folders
            valid_folders = [f for f in species_folder_names if f in all_folders]
            invalid_folders = [f for f in species_folder_names if f not in all_folders]
            
            if invalid_folders:
                print(f"⚠️ Warning: These folders don't exist: {invalid_folders}")
            
            if valid_folders:
                print(f"📂 Processing multiple folders: {valid_folders}")
                return valid_folders
            else:
                print("❌ No valid folders to process")
                return []
        
        else:
            print(f"❌ Invalid species_folder_names type: {type(species_folder_names)}")
            return []



    def load_chunks(self, root_folder: str = Config.DEFAULT_ROOT_FOLDER, 
                   species_folder_names = Config.DEFAULT_SPECIES_FOLDER):
        """Load and chunk documents - your existing function"""
        chunks = []
        folders_to_process = self.get_species_folders(root_folder, species_folder_names)

        root_path = Path(root_folder)

        for species_folder_name in folders_to_process:
            species_folder = root_path / species_folder_name
        
            print(f"\n🔍 Processing folder: {root_folder}/{species_folder_name}")

            if not species_folder.exists() or not species_folder.is_dir():
                print(f"⚠️ Skipping non-existent folder: {species_folder_name}")
                continue

            folder_chunks = 0
        
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
                        stem = filepath.stem.replace(f"{species_folder.name}_", "")[:self.max_filename_length]
                        suffix = filepath.suffix   

                        for doc in raw_docs:
                            doc.page_content = self.clean_text(doc.page_content)
                            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                            pdf_chunks = splitter.split_documents([doc])

                            for idx, subchunk in enumerate(pdf_chunks):
                                subchunk.metadata["species"] = species_folder.name
                                subchunk.metadata["source"] = f"{stem}{suffix}"
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
                            folder_chunks += len(pdf_chunks)

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
                            folder_chunks += len(md_chunks)
                        # pass

                    else:
                        print(f"[!] Skipping unsupported file type: {filepath}")

                print(f"✅ {species_folder_name}: {folder_chunks} chunks processed")

        print(f"\n✅ Total chunks ready: {len(chunks)} (from {len(folders_to_process)} folders)")
        return chunks

    
    def get_chunk_ids(self, chunks):
        """Extract IDs from chunks"""
        return [chunk.metadata.get("doc_tag") for chunk in chunks]
