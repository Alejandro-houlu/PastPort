import argparse
from core.vectordb import VectorDBManager
from core.document_processor import DocumentProcessor
from core.update_manager import UpdateManager
from core.query_engine import QueryEngine


def parse_species_folders(speciesfolder_arg):
    """
    Parse the speciesfolder argument to handle multiple folders.
    
    Args:
        speciesfolder_arg: String that can be:
            - "all" 
            - "folder1,folder2,folder3" (comma-separated)
            - "folder1 folder2 folder3" (space-separated)
            - "folder1" (single folder)
    
    Returns:
        Parsed folder specification (string "all" or list of folders)
    """
    if not speciesfolder_arg:
        return "dinosaur_sauropod"  # default
    
    # Handle "all" case
    if speciesfolder_arg.lower().strip() == "all":
        return "all"
    
    # Try comma-separated first
    if ',' in speciesfolder_arg:
        folders = [f.strip() for f in speciesfolder_arg.split(',') if f.strip()]
        return folders if len(folders) > 1 else folders[0] if folders else "dinosaur_sauropod"
    
    # Try space-separated (but be careful with shell parsing)
    folders = speciesfolder_arg.split()
    if len(folders) > 1:
        return folders
    
    # Single folder
    return speciesfolder_arg.strip()


def main():
    parser = argparse.ArgumentParser(description="RAG System Manager")
    parser.add_argument('--mode', choices=['init', 'load', 'update', 'query', 'info', 'delete_chunks', 'delete_collection'], 
                       required=True, help="Operation mode")
    parser.add_argument('--rootfolder', default="data", help="Root folder")
    parser.add_argument('--speciesfolder', default="dinosaur_sauropod", help='Species folder(s) to process. Options: "all", "folder1,folder2,folder3", or "single_folder"')
    parser.add_argument('--question', help="Question to ask (for query mode)")
    parser.add_argument('--doc_tags', nargs='+', help="Doc_tags to delete (space-separated)")
    
    args = parser.parse_args()

    # Parse species folders
    species_folders = parse_species_folders(args.speciesfolder)
    
    # Initialize components
    vectordb = VectorDBManager()
    processor = DocumentProcessor()
    
    if args.mode == 'init':
        print("🚀 Initializing vector database...")
        vectordb.initialize()
        
    elif args.mode == 'load':
        print("📚 Loading documents...")
        print(f"📁 Root folder: {args.rootfolder}")
        print(f"🎯 Target folders: {species_folders}")
        vectordb.initialize()
        chunks = processor.load_chunks(args.rootfolder, species_folders)

        if chunks:
            update_manager = UpdateManager(vectordb.vdb, processor)
            update_manager.add_chunks(chunks)
        
    elif args.mode == 'update':
        print("🔄 Checking for updates...")
        print(f"📁 Root folder: {args.rootfolder}")
        print(f"🎯 Target folders: {species_folders}")

        vectordb.initialize()
        update_manager = UpdateManager(vectordb.vdb, processor)
        # update_manager.check_for_updates(args.rootfolder, args.speciesfolder)

        if isinstance(species_folders, list):
            for folder in species_folders:
                print(f"\n--- Checking updates for: {folder} ---")
                update_manager.check_for_updates(args.rootfolder, folder)
        else:
            update_manager.check_for_updates(args.rootfolder, species_folders)
        
    elif args.mode == 'query':
        # if not args.question:
        #     args.question = input("❓ Enter your question: ")
        
        # print("🔍 Querying...")
        # vectordb.initialize()
        # query_engine = QueryEngine(vectordb.vdb)
        # result = query_engine.query(args.question)
        # print(result)

        vectordb.initialize()
        query_engine = QueryEngine(vectordb.vdb)

        print("💬 Ask me any questions!")
        print("💡 Type 'quit', 'exit', or 'q' to stop")
        print("-" * 50)
        
        while True:
            try:
                question = input("\n❓ Enter your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q', '']:
                    print("👋 Thanks for chatting!")
                    break

                results = query_engine.query(question)
                
                if not results:
                    print("❌ No results found. Try rephrasing your question.")

                print(print(f"{results['c']}\n\n---\n\n💭 THOUGHT: {results['t']}\n\n🖋️ ANSWER: {results['a']}\n\nℹ️ SOURCES: {results['s']}"))
                
                print("\n" + "="*50)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

                
    elif args.mode == 'info':
        vectordb.initialize()
        info = vectordb.get_collection_info()
        if info:
            print(f"📊 Collection: {info['name']}")
            print(f"📄 Documents: {info['id_counts']}")

    elif args.mode == 'delete_chunks':
        vectordb.initialize()
        
        if args.doc_tags:
            # Use chunk IDs from command line
            user_input_chunks = args.doc_tags
            chunk_ids_to_delete = [tag.strip() for tag in user_input_chunks]

            # Show existing chunks
            existing_data = vectordb.vdb.get(include=['metadatas'])
            existing_tags = set([metadata['doc_tag'] for metadata in existing_data['metadatas']])

            valid_tags = [id for id in chunk_ids_to_delete if id in existing_tags]
            invalid_tags = [id for id in chunk_ids_to_delete if id not in existing_tags]
        
            if invalid_tags:
                print(f"⚠️ Warning: These chunk IDs don't exist: {invalid_tags}")
            
            if not valid_tags:
                print("❌ No valid chunk IDs to delete.")
                return
            
            # Show what will be deleted
            print(f"\n🗑️ Will delete {len(valid_tags)} chunks:")
            for i, doc_tag in enumerate(valid_tags[:10]):
                print(f"  {i+1}. {doc_tag}")
            if len(valid_tags) > 10:
                print(f"  ... and {len(valid_tags) - 10} more")
            
            # Confirm deletion
            if valid_tags:  # Only ask for confirmation in interactive mode
               confirm = input(f"\n❓ Are you sure you want to delete these {len(valid_tags)} chunks? (y/n): ").lower()
               if confirm != 'y':
                print("❌ Deletion cancelled.")
                return
            
            # Perform deletion
            try:
                vectordb.vdb.delete(ids=valid_tags)
                print(f"✅ Successfully deleted {len(valid_tags)} chunks!")
                
                # Show updated stats
                updated_data = vectordb.vdb.get()
                remaining_count = len(updated_data['ids'])
                print(f"📊 Remaining chunks: {remaining_count}")
                
            except Exception as e:
                print(f"❌ Error deleting chunks: {e}")



    elif args.mode == 'delete_collection':
        vectordb.initialize()
        info = vectordb.get_collection_info()
        current_collection = info['name']
        vectordb.vdb.delete_collection()
        print(f"🗑️ '{current_collection}' has been deleted.")
   

if __name__ == "__main__":
    main()