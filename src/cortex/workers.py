from cortex.agents.level1_comprehension import ComprehensionAgent
from cortex.agents.level3_curation.corpus_curator import CorpusCuratorAgent
from cortex.services.chroma_service import ChromaService
from cortex.services.knowledge_graph_service import KnowledgeGraphService
from cortex.models.events import GitCommitEvent, CodeChangeEvent
from cortex.models.insights import Insight
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event_task(ctx, event_data:dict):
    """
    ARQ task to process an event.
    """
    agent = ComprehensionAgent()
    insight: Insight | None = None

    event_type = event_data.get("event_type")
    if event_type == "git_commit":
        event = GitCommitEvent(**event_data)
        insight = await agent.process_git_commit_event(event)
    elif event_type == "file_change":
        event = CodeChangeEvent(**event_data)
        insight = await agent.process_code_change_event(event)
    else:
        logger.info(f"Unknown event type: {event_type}")

    if insight:
        # 1. Persist to the human-readable knowledge graph
        kg_service = KnowledgeGraphService()
        kg_service.process_insight(insight)

        # 2. Persist to the machine-readable vector DB
        chroma_service = ChromaService()
        chroma_service.add_document(
            doc_id=insight.insight_id,
            content=insight.content_for_embedding,
            metadata=insight.metadata
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
