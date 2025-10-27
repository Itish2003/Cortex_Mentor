from cortex.pipelines.processors import Processor
from cortex.models.insights import Insight
import logging
from cortex.services.chroma_service import ChromaService
from cortex.services.upstash_service import UpstashService
from cortex.services.llmservice import LLMService
from cortex.pipelines.curation import CurationProcessor
from pydantic import BaseModel
from logging import Logger
logger: Logger = logging.getLogger(__name__)
from cortex.services.prompt_manager import PromptManager


from google.adk.agents import LlmAgent
from cortex.utility.agent_runner import run_standalone_agent

from cortex.pipelines.pipelines import Pipeline
from cortex.core.config import Settings
from cortex.pipelines.graph_traversal import GraphTraversalProcessor

class RunPrivatePipeline(Processor):
    def __init__(self, chroma_service: ChromaService, settings: Settings):
        self.pipeline = Pipeline([
            PrivateKnowledgeQuerier(chroma_service),
            GraphTraversalProcessor(knowledge_graph_root=settings.knowledge_graph_path),
        ])

    async def process(self, data: str, context: dict) -> dict:
        private_results = await self.pipeline.execute(data, context)
        return {"private_knowledge": private_results}

class RunPublicPipeline(Processor):
    def __init__(self, upstash_service: UpstashService, llm_service: LLMService):
        self.pipeline = Pipeline([
            PublicKnowledgeQuerier(upstash_service),
            KnowledgeGatewayProcessor(llm_service),
            CurationTriggerProcessor(llm_service, upstash_service),
        ])

    async def process(self, data: str, context: dict) -> dict:
        public_results = await self.pipeline.execute(data, context)
        return {"public_knowledge": public_results}

def create_synthesis_pipeline(chroma_service: ChromaService, upstash_service: UpstashService, llm_service: LLMService) -> Pipeline:
    settings = Settings()
    return Pipeline([
        # Running these in parallel
        [
            RunPrivatePipeline(chroma_service, settings),
            RunPublicPipeline(upstash_service, llm_service),
        ],
        InsightSynthesizer(llm_service),
    ])

class PrivateKnowledgeQuerier(Processor):
    """
    Queries the private ChromaDB knowledge store.
    """
    def __init__(self, chroma_service: ChromaService):
        self.chroma_service = chroma_service

    async def process(self, data: str, context: dict) -> dict:
        logger.info("Querying private knowledge store (ChromaDB)...")
        private_results = self.chroma_service.query(data, n_results=2)
        return {
            "query_text": data,
            "private_results": private_results
        }

class PublicKnowledgeQuerier(Processor):
    """
    Queries the public Upstash knowledge store.
    """
    def __init__(self, upstash_service: UpstashService):
        self.upstash_service = upstash_service

    async def process(self, data: str, context: dict) -> dict:
        logger.info("Querying public knowledge store (Upstash)...")
        public_results = await self.upstash_service.query(data, n_results=2)
        return {
            "public_results": public_results, 
            "query_text": data
    }

class GatewayDecision(BaseModel):
    needs_improvement: bool

class KnowledgeGatewayProcessor(Processor):
    """
    A gateway processor that uses an LLM agent to decide if knowledge needs improvement.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompt_manager = PromptManager()
        self.gateway_agent = LlmAgent(
            name="knowledge_gateway_agent",
            instruction=self.prompt_manager.render("knowledge_gateway.jinja2"),
            output_schema=GatewayDecision,
            model=llm_service.settings.gemini_flash_model,
        )

    async def process(self, data: dict, context: dict) -> dict:
        logger.info("Evaluating retrieved public knowledge...")
        query_text = data["query_text"]
        public_results = data.get("public_results", [])
        public_context = "\n".join([str(r) for r in public_results])

        prompt = self.prompt_manager.render(
            "knowledge_gateway.jinja2",
            query_text=query_text,
            public_context=public_context
        )
        
        evaluation_str = await run_standalone_agent(self.gateway_agent, prompt)
        
        try:
            gateway_decision = GatewayDecision.model_validate_json(evaluation_str)
            decision = gateway_decision.needs_improvement
        except Exception:
            # Fallback for non-json response
            if "true" in evaluation_str.lower() or "NEEDS_IMPROVEMENT" in evaluation_str:
                decision = True
            else:
                decision = False

        logger.info(f"Knowledge evaluation result: {decision}")
        data["needs_improvement"] = decision
        return data

class CurationTriggerProcessor(Processor):
    """
    Triggers the curation pipeline if the knowledge needs improvement.
    """
    def __init__(self, llm_service: LLMService, upstash_service: UpstashService):
        self.llm_service = llm_service
        self.upstash_service = upstash_service

    async def process(self, data: dict, context: dict) -> dict:
        needs_improvement = data.get("needs_improvement", False)
        if needs_improvement:
            logger.info("Knowledge needs improvement. Triggering curation pipeline...")
            curation_processor = CurationProcessor(self.upstash_service, self.llm_service)
            data = await curation_processor.process(data, context)
        else:
            logger.info("Knowledge is sufficient.")
        return data

class InsightSynthesizer(Processor):
    """
    Synthesizes the final insight from all gathered knowledge.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompt_manager = PromptManager()

    async def process(self, data: dict, context: dict) -> dict:
        logger.info("Synthesizing final insight...")
        private_knowledge = data.get("private_knowledge", {})
        public_knowledge = data.get("public_knowledge", {})

        private_results = private_knowledge.get("private_results")
        traversed_knowledge = private_knowledge.get("traversed_knowledge")
        public_results = public_knowledge.get("public_results")
        augmented_knowledge = public_knowledge.get("augmented_knowledge")

        prompt = self.prompt_manager.render(
            "insight_synthesis.jinja2",
            private_results=private_results,
            traversed_knowledge=traversed_knowledge,
            public_results=public_results,
            augmented_knowledge=augmented_knowledge
        )

        final_insight = self.llm_service.generate(prompt, model=self.llm_service.settings.gemini_pro_model)
        data["final_insight"] = final_insight

        logger.info(f"Final Insight: {final_insight}")
        return data
