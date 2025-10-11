from arq import task
from cortex.agents.level1_comprehension import ComprehensionAgent
from cortex.agents.level3_curation.corpus_curator import CorpusCuratorAgent
from cortex.services.chroma_service import ChromaService

@task
async def process_event_task(ctx, event_data):
    """
    ARQ task to process an event.
    """
    agent = ComprehensionAgent()
    processed_data = await agent.process_event(event_data)
    chroma_service = ChromaService()
    chroma_service.add_document(
        doc_id=processed_data.get("id"),
        content=processed_data.get("content"),
        metadata=processed_data.get("metadata", {})
    )

@task
async def curate_corpus_task(ctx, data):
    """

    ARQ task to curate and save data to the public MCP knowledge base.
    """
    agent = CorpusCuratorAgent()
    await agent.curate_and_save(data)

class WorkerSettings:
    functions = [process_event_task, curate_corpus_task]
    queues = ['high_priority', 'low_priority']
