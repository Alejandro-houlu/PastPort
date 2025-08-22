from langchain_chroma import Chroma
from tqdm import tqdm

class UpdateManager:
    def __init__(self, vectordb_manager, document_processor):
        self.vectordb = vectordb_manager
        self.processor = document_processor
    
    def check_for_updates(self, root_folder: str, species_folders):
        """Check for new documents and prompt user"""
        print("🔍 Checking for new documents...")
        
        # Load potential new chunks
        new_chunks = self.processor.load_chunks(root_folder, species_folders)
        new_ids = self.processor.get_chunk_ids(new_chunks)
        
        # Get existing IDs from database
        existing_data = self.vectordb.get(include=['metadatas'])
        existing_tags = set([metadata['doc_tag'] for metadata in existing_data['metadatas']])
        # existing_ids = set(existing_data['ids'])
        
        # Find truly new chunks
        really_new_ids = [id for id in new_ids if id not in existing_tags]
        really_new_chunks = [chunk for chunk in new_chunks 
                           if chunk.metadata.get("doc_tag") in really_new_ids]
        
        if len(existing_tags):
            print(f"📝 Existing number of chunks: {len(existing_tags)}")

        if not really_new_chunks:
            print("✅ No new documents found.")
            return False
        
        # # Show user what will be added
        # print(f"\n✨ Found {len(really_new_chunks)} new chunks:")
        # for i, chunk in enumerate(really_new_chunks):
        #     if i < 10:  
        #         print(f"  {i+1}. {chunk.metadata.get('doc_tag')}...")
        
        # if len(really_new_chunks) > 5:
        #     print(f"  ... and {len(really_new_chunks) - 5} more")



        # Show breakdown by species
        species_breakdown = {}
        for chunk in really_new_chunks:
            species = chunk.metadata.get('species', 'unknown')
            species_breakdown[species] = species_breakdown.get(species, 0) + 1
        
        # Show user what will be added
        print(f"\n✨ Found {len(really_new_chunks)} new chunks:")
        
        # Show species breakdown
        if len(species_breakdown) > 1:
            print("📂 By species:")
            for species, count in sorted(species_breakdown.items()):
                print(f"  • {species}: {count} chunks")
        
        # Show sample chunks
        print(f"\n📄 Sample chunks:")
        for i, chunk in enumerate(really_new_chunks[:10]):
            print(f"  {i+1}. {chunk.metadata.get('doc_tag')}")


        
        # Prompt user
        response = input(f"\n❓ Add these {len(really_new_chunks)} new chunks? (y/n): ").lower()
        
        if response == 'y':
            return self.add_chunks(really_new_chunks)
        else:
            print("❌ Update cancelled.")
            return False
    
    def add_chunks(self, chunks):
        """Add chunks to the database"""
        try:
            # documents = [chunk.page_content for chunk in chunks]
            # metadatas = [chunk.metadata for chunk in chunks]
            # ids = [chunk.metadata.get("doc_tag") for chunk in chunks]
            
            # self.vectordb.add_documents(
            #     chunks,
            #     ids=ids
            # )

            # Show what's being added
            species_breakdown = {}
            for chunk in chunks:
                species = chunk.metadata.get('species', 'unknown')
                species_breakdown[species] = species_breakdown.get(species, 0) + 1
            
            if len(species_breakdown) > 1:
                print(f"📂 Adding chunks for {len(species_breakdown)} species:")
                for species, count in sorted(species_breakdown.items()):
                    print(f"  • {species}: {count} chunks")



            for i in tqdm(range(0, len(chunks), 10), desc="🔄 Uploading"):
                batch = chunks[i:i+10]
                # batch_ids = ids[i:i+10]

                self.vectordb.add_documents(batch)
            
            print(f"✅ Successfully added {len(chunks)} new chunks!")

            existing_data_updated = self.vectordb.get(include=['metadatas'])
            existing_tags_updated = set([metadata['doc_tag'] for metadata in existing_data_updated['metadatas']])         

            print(f"✅ Updated number of chunks: {len(existing_tags_updated)}")


            # Show species breakdown after update
            species_count = {}
            for metadata in existing_data_updated['metadatas']:
                species = metadata.get('species', 'unknown')
                species_count[species] = species_count.get(species, 0) + 1
            
            if len(species_count) > 1:
                print("\n📂 Current species breakdown:")
                for species, count in sorted(species_count.items()):
                    print(f"  • {species}: {count} chunks")


            return True
        except Exception as e:
            print(f"❌ Error adding chunks: {e}")
            return False