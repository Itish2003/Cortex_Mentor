from cortex.pipelines.processors import Processor
from cortex.services.upstash_service import UpstashService
from cortex.services.llmservice import LLMService
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from cortex.utility.agent_runner import run_standalone_agent
from google.adk.tools import FunctionTool
import logging
import uuid
from google.adk.tools.google_search_agent_tool import create_google_search_agent
from cortex.services.prompt_manager import PromptManager

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

def create_curation_agent(upstash_service: UpstashService, llm_service: LLMService) -> SequentialAgent:
    upstash_writer = UpstashWriter(upstash_service)
    prompt_manager = PromptManager()

    async def UpstashWriterTool(data: str) -> str:
        """Writes the given data to the Upstash knowledge base."""
        return await upstash_writer.write(data)

    web_searcher = create_google_search_agent(model=llm_service.settings.gemini_flash_model)

    security_analyst = LlmAgent(
        name="security_analyst",
        instruction="You are a security analyst. Analyze the provided text for any security implications, vulnerabilities, or best practices. Summarize your findings.",
        model=llm_service.settings.gemini_flash_model,
    )

    best_practices_analyst = LlmAgent(
        name="best_practices_analyst",
        instruction="You are a software architect. Analyze the provided text for software development best practices, design patterns, or architectural principles. Summarize your findings.",
        model=llm_service.settings.gemini_flash_model,
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
            if event.author == web_searcher.name and event.is_final_response() and event.content and event.content.parts:
                web_search_results = "".join([part.text for part in event.content.parts if part.text])
            if event.author == "security_analyst" and event.is_final_response() and event.content and event.content.parts:
                security_analysis = "".join([part.text for part in event.content.parts if part.text])
            if event.author == "best_practices_analyst" and event.is_final_response() and event.content and event.content.parts:
                best_practices_analysis = "".join([part.text for part in event.content.parts if part.text])
        
        prompt = prompt_manager.render(
            "chief_editor.jinja2",
            web_search_results=web_search_results,
            security_analysis=security_analysis,
            best_practices_analysis=best_practices_analysis
        )

        llm_request.contents = [types.Content(parts=[types.Part(text=prompt)])]

    chief_editor = LlmAgent(
        name="chief_editor",
        instruction="This will be replaced by the callback.",
        model=llm_service.settings.gemini_pro_model,
        tools=[FunctionTool(func=UpstashWriterTool)],
        before_model_callback=chief_editor_callback,
    )

    curation_agent = SequentialAgent(
        name="curation_agent",
        sub_agents=[web_searcher, parallel_analyzer, chief_editor],
    )

    return curation_agent

class CurationProcessor(Processor):
    def __init__(self, upstash_service: UpstashService, llm_service: LLMService):
        # FIX: Removed self.curation_agent instantiation from __init__
        self.upstash_service = upstash_service
        self.llm_service = llm_service

    async def process(self, data: dict, context: dict) -> dict:
        query_text = data["query_text"]
        logger.info(f"Starting curation process for query: {query_text}")

        # FIX: Create the complex agent hierarchy specific to this request
        curation_agent = create_curation_agent(self.upstash_service, self.llm_service)

        # Run the full curation pipeline to get the final, synthesized result
        final_summary = await run_standalone_agent(
            curation_agent,
            query_text,
            target_agent_name="chief_editor"
        )

        # Immediately add the augmented knowledge to the data dictionary
        data["augmented_knowledge"] = final_summary

        return data
