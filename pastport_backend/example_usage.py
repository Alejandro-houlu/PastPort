#!/usr/bin/env python3
"""
Example usage of the PastPort Museum RAG package.

This script demonstrates how to use the package programmatically
within the FastAPI backend or other Python applications.
"""

import os
from pastport_museum_rag import VectorDBManager, DocumentProcessor, QueryEngine

def main():
    print("🚀 PastPort Museum RAG - Example Usage")
    print("=" * 50)
    
    # Optional: Set environment variables
    # os.environ["PASTPORT_CHROMA_DB_PATH"] = "./example_chroma"
    # os.environ["PASTPORT_COLLECTION_NAME"] = "example_collection"
    
    try:
        # 1. Initialize VectorDB
        print("\n1️⃣ Initializing Vector Database...")
        vdb_manager = VectorDBManager()
        success = vdb_manager._initialize()
        
        if not success:
            print("❌ Failed to initialize vector database")
            return
        
        # 2. Get collection info
        print("\n2️⃣ Getting Collection Info...")
        info = vdb_manager.get_collection_info()
        if info:
            print(f"📊 Collection: {info['name']}")
            print(f"📄 Document count: {info['id_counts']}")
        
        # 3. Process documents (if data exists)
        print("\n3️⃣ Document Processing Example...")
        processor = DocumentProcessor()
        
        # Example: Load documents from a specific folder
        # Uncomment and modify path as needed
        # doc_count = processor.process_and_add_documents(
        #     vdb_manager, 
        #     "./data", 
        #     "rafflesia"
        # )
        # print(f"✅ Processed {doc_count} documents")
        
        # 4. Query the system
        print("\n4️⃣ Query Example...")
        if info and info['id_counts'] > 0:
            query_engine = QueryEngine(vdb_manager.vdb)
            
            # Example query
            question = "Tell me about the dinos in LKC museum?"
            print(f"❓ Question: {question}")
            
            result = query_engine.query(question)
            print(f"🖋️ Answer: {result.answer}")
            print(f"📚 Found {len(result.contexts)} relevant contexts")
            
            # Show context sources
            if result.contexts:
                print("\n📖 Sources:")
                for i, context in enumerate(result.contexts[:3]):
                    print(f"  {i+1}. {context['source']} (score: {context['score']:.3f})")
        else:
            print("ℹ️ No documents in database. Load some documents first using:")
            print("   python -m pastport_museum_rag.cli --mode load --rootfolder=../data --speciesfolder=rafflesia")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
