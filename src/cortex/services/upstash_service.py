
import os
from upstash_vector import Index

class UpstashService:
    def __init__(self):
        # Bypass pydantic-settings and load directly from the environment
        url = os.getenv("UPSTASH_URL", "")
        token = os.getenv("UPSTASH_TOKEN", "")

        print(f"--- Initializing UpstashService ---")
        print(f"URL from os.getenv: '{url}'")
        print(f"Token from os.getenv starts with: '{token[:5]}...'")
        print(f"---------------------------------")

        self.index = Index(url=url, token=token)

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
