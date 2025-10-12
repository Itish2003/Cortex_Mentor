from cortex.core.config import Settings
import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import EmbeddingFunction, Embeddings, Embeddable
import requests

class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model="nomic-embed-text:v1.5"):
        self.model = model

    def __call__(self, texts: Embeddable) -> Embeddings:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []
        for text in texts:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            embeddings.append(response.json()["embedding"])
        return embeddings


class ChromaService:
    def __init__(self):
        settings = Settings()
        self.client = chromadb.PersistentClient(path=settings.chromadb_path)
        self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        self.collection = self.client.get_or_create_collection(
            name="private_user_model",
            embedding_function=OllamaEmbeddingFunction()
        )
       

    def add_document(self, doc_id: str, content: str, metadata: dict):
        """Add a document to the ChromaDB collection."""
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )

    def query(self, query_text: str, n_results: int = 3):
        """Query the collection for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results