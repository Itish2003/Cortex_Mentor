from cortex.pipelines.processors import Processor
from cortex.services.upstash_service import UpstashService
from cortex.services.llmservice import LLMService
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, CallbackContext
from google.adk.models.llm_request import LlmRequest
from cortex.utility.agent_runner import run_standalone_agent
from google.adk.tools import FunctionTool, google_search
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)

class UpstashWriter:
    def __init__(self, upstash_service: UpstashService):
        self.upstash_service = upstash_service

    async def write(self, data: str) -> str:
        logger.info(f"Writing data to Upstash: {data}")
        doc_id = str(uuid.uuid4())
        metadata = {"source": "web_search_curation"}
        await self.upstash_service.add_document(doc_id=doc_id, content=data, metadata=metadata)
        return "Successfully wrote data to Upstash."

from google.adk.tools.google_search_agent_tool import create_google_search_agent

def create_curation_agent(upstash_service: UpstashService, llm_service: LLMService) -> SequentialAgent:
    upstash_writer = UpstashWriter(upstash_service)

    async def UpstashWriterTool(data: str) -> str:
        """Writes the given data to the Upstash knowledge base."""
        return await upstash_writer.write(data)

    web_searcher = create_google_search_agent(model=llm_service.model)

    security_analyst = LlmAgent(
        name="security_analyst",
        instruction="You are a security analyst. Analyze the provided text for any security implications, vulnerabilities, or best practices. Summarize your findings.",
        model=llm_service.model,
    )

    best_practices_analyst = LlmAgent(
        name="best_practices_analyst",
        instruction="You are a software architect. Analyze the provided text for software development best practices, design patterns, or architectural principles. Summarize your findings.",
        model=llm_service.model,
    )

    parallel_analyzer = ParallelAgent(
        name="parallel_analyzer",
        sub_agents=[security_analyst, best_practices_analyst],
    )

    async def chief_editor_callback(callback_context: CallbackContext, llm_request: LlmRequest):
        web_search_results = ""
        security_analysis = ""
        best_practices_analysis = ""

        for event in callback_context.session.events:
            if event.author == "web_searcher" and event.is_final_response():
                web_search_results = "".join([part.text for part in event.content.parts if part.text])
            if event.author == "security_analyst" and event.is_final_response():
                security_analysis = "".join([part.text for part in event.content.parts if part.text])
            if event.author == "best_practices_analyst" and event.is_final_response():
                best_practices_analysis = "".join([part.text for part in event.content.parts if part.text])
        
        prompt = f"""You are a chief editor. You have received a summary of a topic from a web search, and analyses from a security analyst and a best practices analyst.
        Your job is to synthesize all of this information into a single, coherent, and high-quality summary that is ready to be saved to a knowledge base.

        Web Search Results:
        {web_search_results}

        Security Analysis:
        {security_analysis}

        Best Practices Analysis:
        {best_practices_analysis}

        Synthesize these into a final, comprehensive summary."""

        llm_request.contents = [prompt]

    chief_editor = LlmAgent(
        name="chief_editor",
        instruction="This will be replaced by the callback.",
        model=llm_service.model,
        before_model_callback=chief_editor_callback,
    )

    curation_agent = SequentialAgent(
        name="curation_agent",
        sub_agents=[web_searcher, parallel_analyzer, chief_editor],
    )

    return curation_agent

class CurationProcessor(Processor):
    def __init__(self, upstash_service: UpstashService, llm_service: LLMService):
        self.curation_agent = create_curation_agent(upstash_service, llm_service)
        self.llm_service = llm_service

    async def process(self, data: dict, context: dict) -> dict:
        query_text = data["query_text"]
        logger.info(f"Starting curation process for query: {query_text}")

        # Run the full curation pipeline to get the final, synthesized result
        final_summary = await run_standalone_agent(
            self.curation_agent,
            query_text,
            target_agent_name="chief_editor"
        )

        # Immediately add the augmented knowledge to the data dictionary
        data["augmented_knowledge"] = final_summary

        # Create a background task to write the final summary to the knowledge base
        async def write_to_knowledge_base():
            logger.info("Starting background task to write to knowledge base...")
            upstash_writer = UpstashWriter(self.upstash_service)
            await upstash_writer.write(final_summary)
            logger.info("Background task to write to knowledge base finished.")

        asyncio.create_task(write_to_knowledge_base())

        return data
