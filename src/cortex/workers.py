from cortex.agents.level1_comprehension import ComprehensionAgent
from cortex.agents.level3_curation.corpus_curator import CorpusCuratorAgent
from cortex.services.chroma_service import ChromaService
from cortex.models.events import GitCommitEvent, CodeChangeEvent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event_task(ctx, event_data:dict):
    """
    ARQ task to process an event.
    """
    agent = ComprehensionAgent()
    processed_data = None

    event_type = event_data.get("event_type")
    if event_type == "git_commit":
        event = GitCommitEvent(**event_data)
        processed_data = await agent.process_git_commit_event(event)
    elif event_type == "file_change":
        event = CodeChangeEvent(**event_data)
        processed_data = await agent.process_code_change_event(event)
        logger.info(f"Processing file change event for {event.file_path}")
    else:
        logger.info(f"Unknown event type: {event_type}")

    if processed_data:
        chroma_service = ChromaService()
        doc_id = processed_data.get("id")
        content = processed_data.get("content")
        metadata = processed_data.get("metadata", {}) # Default to empty dict

        # 3. Ensure the required fields are not None before saving
        if doc_id and content:
            chroma_service = ChromaService()
            chroma_service.add_document(
                doc_id=doc_id,
                content=content,
                metadata=metadata
            )

async def curate_corpus_task(ctx, data):
    """

    ARQ task to curate and save data to the public MCP knowledge base.
    """
    agent = CorpusCuratorAgent()
    await agent.curate_and_save(data)

class WorkerSettings:
    functions = [process_event_task, curate_corpus_task]
    queues = ['high_priority', 'low_priority']
