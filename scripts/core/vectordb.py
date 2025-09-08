# from langchain.vectorstores.chroma import Chroma
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config.settings import Config
from chromadb.config import Settings

class GetEmbeddings:
    def __init__(self, model: str = Config.EMBEDDING_MODEL):
        self.model = model
        self.embeddings = OllamaEmbeddings(model=model)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]: #check this
        return self.embeddings.embed_query(text)


class VectorDBManager:
    def __init__(self, db_path: str = Config.CHROMA_DB_PATH, 
                 collection_name: str = Config.COLLECTION_NAME):
        self.db_path = db_path
        self.collection_name = collection_name
        self.vdb = None
        self.embedding_function = GetEmbeddings()
    
    def initialize(self):
        """Initialize the vector database"""
        try:
            client_settings = Settings(anonymized_telemetry=False, is_persistent=True)
            self.vdb = Chroma(collection_name=self.collection_name, embedding_function=self.embedding_function,
                               persist_directory=self.db_path, client_settings=client_settings)
            print(f"✅ VectorDB initialized: {self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error initializing VectorDB: {e}")
            return False
    
    def get_collection_info(self):
        """Get collection statistics"""
        if self.vdb:
            return {
                "name": self.collection_name,
                "id_counts": len(self.vdb.get()['ids']),
            }
        return None