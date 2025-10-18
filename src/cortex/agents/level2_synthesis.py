
from cortex.services.chroma_service import ChromaService
from cortex.services.upstash_service import UpstashService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SynthesisAgent:
    def __init__(self):
        self.chroma_service = ChromaService()
        self.upstash_service = UpstashService()

    async def synthesize_insights(self, query_text: str):
        """
        Synthesizes insights from both the private user model and the public MCP knowledge base.
        1. Queries both private and public knowledge stores.
        2. Synthesizes the findings into a higher-level insight.
        """
        logger.info("Querying private knowledge store (ChromaDB)...")
        private_results = self.chroma_service.query(query_text,n_results=2)
        logger.info("Querying public knowledge store (Upstash)...")
        public_results = self.upstash_service.query(query_text,n_results=2)

        # In a real implementation, this method would involve
        # a more sophisticated merging and ranking of the results.
        combined_results = {
            "private": private_results,
            "public": public_results
        }
        logger.info("Synthesis Results: %s", combined_results)
        return combined_results
