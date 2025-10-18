
from upstash_vector import AsyncIndex, Vector
from cortex.core.config import Settings

class UpstashService:
    def __init__(self):
        settings = Settings()
        self.index = AsyncIndex(url=settings.upstash_url, token=settings.upstash_token)

    async def add_document(self, doc_id: str, content: str, metadata: dict):
        """Add a document to the Upstash collection, letting Upstash generate the embedding."""
        try:
            await self.index.upsert(
                vectors=[
                    Vector(id=doc_id, vector=[], metadata=metadata, data=content)
                ]
            )
        except Exception as e:
            print(f"[UpstashService] Error adding document {doc_id}: {e}")

    async def query(self, query_text: str, n_results: int = 3):
        """Query the collection for similar documents, letting Upstash generate the embedding."""
        results = await self.index.query(
            data=query_text, # Send the raw text, not a vector
            top_k=n_results,
            include_metadata=True
        )
        return results
