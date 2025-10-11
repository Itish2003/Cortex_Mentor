
from cortex.services.chroma_service import ChromaService
from cortex.services.upstash_service import UpstashService

class SynthesisAgent:
    def __init__(self):
        self.chroma_service = ChromaService()
        self.upstash_service = UpstashService()

    async def synthesize_insights(self, query_text: str):
        """
        Synthesizes insights from both the private user model and the public MCP knowledge base.
        """
        private_results = self.chroma_service.query(query_text)
        public_results = self.upstash_service.query(query_text)

        # In a real implementation, this method would involve
        # a more sophisticated merging and ranking of the results.
        combined_results = {
            "private": private_results,
            "public": public_results
        }

        return combined_results
