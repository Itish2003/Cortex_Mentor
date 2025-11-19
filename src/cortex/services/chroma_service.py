from cortex.core.config import Settings
import chromadb
import requests
from typing import List

# This is now a standalone helper class, not a ChromaDB type.
class OllamaEmbeddingHelper:
    def __init__(self, model="nomic-embed-text:v1.5"):
        self.model = model
        self.settings = Settings()

    def get_embedding(self, text: str) -> List[float]:
        """Generates a single embedding for a single piece of text."""
        response = requests.post(
            self.settings.llm_embed_url,
            json={"model": self.model, "input": text}
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

class ChromaService:
    def __init__(self):
        settings = Settings()
        self.client = chromadb.PersistentClient(path=settings.chromadb_path)
        # Create the collection WITHOUT an embedding function.
        self.collection = self.client.get_or_create_collection(
            name="private_user_model"
        )
        # Create an instance of our helper for use in the add_document method.
        self.embedding_helper = OllamaEmbeddingHelper()

    def add_document(self, doc_id: str, content: str, metadata: dict):
        """
        Manually generates an embedding and then adds the document to the collection.
        """
        # 1. Manually generate the embedding for the document content.
        embedding = self.embedding_helper.get_embedding(content)

        # 2. Add the document, but this time provide the pre-computed embedding.
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding], # Pass the vector directly
            documents=[content],
            metadatas=[metadata]
        )

    def query(self, query_text: str, n_results: int = 3):
        """Query the collection for similar documents."""
        # For querying, we must also generate an embedding for the query text first.
        query_embedding = self.embedding_helper.get_embedding(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
        return results