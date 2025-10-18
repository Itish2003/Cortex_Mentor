
from upstash_vector import Index
from cortex.core.config import Settings

class UpstashService:
    def __init__(self):
        settings = Settings()
        print(f"--- Initializing UpstashService ---")
        print(f"URL: '{settings.upstash_url}'")
        print(f"Token starts with: '{settings.upstash_token[:5]}...'")
        print(f"---------------------------------")
        self.index = Index(url=settings.upstash_url, token=settings.upstash_token)

    def add_document(self, doc_id: str, content: str, metadata: dict):
        """Add a document to the Upstash collection."""
        self.index.upsert(
            vectors=[
                {"id": doc_id, "vector": [], "metadata": metadata}
            ]
        )

    def query(self, query_text: str, n_results: int = 3):
        """Query the collection for similar documents."""
        results = self.index.query(
            vector=[],
            top_k=n_results,
            include_metadata=True
        )
        return results
