from cortex.agents.level3_curation.corpus_curator import CorpusCuratorAgent
from cortex.models.insights import Insight
import logging
from cortex.core.redis import get_redis
from cortex.agents.level2_synthesis import SynthesisAgent
from cortex.pipelines.pipelines import Pipeline
from cortex.pipelines.comprehension import (
    EventDeserializer,
    InsightGenerator,
    KnowledgeGraphWriter,
    ChromaWriter,
    SynthesisTrigger
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event_task(ctx, event_data: dict):
    """
    ARQ task to process a raw event using the new pipeline architecture.
    """
    logger.info(f"--- Starting Comprehension Pipeline for Event ---")

    comprehension_pipeline = Pipeline([
        EventDeserializer(),
        InsightGenerator(),
        KnowledgeGraphWriter(),
        ChromaWriter(),
        SynthesisTrigger(),
    ])

    context = {}

    try:
        await comprehension_pipeline.execute(
            data=event_data,
            context=context
        )
        logger.info(f"--- Comprehension Pipeline Finished Successfully ---")
    except Exception as e:
        logger.error(f"Comprehension pipeline failed: {e}", exc_info=True)


async def curate_corpus_task(ctx, data):
    """

    ARQ task to curate and save data to the public MCP knowledge base.
    """
    agent = CorpusCuratorAgent()
    await agent.curate_and_save(data)

async def synthesis_task(ctx, query_text: str):
    """
    ARQ task to perform synthesis on the given query text.
    """
    logger.info(f"Synthesizing information for query: {query_text[:50]}...")
    agent = SynthesisAgent()
    await agent.synthesize_insights(query_text)

class WorkerSettings:
    functions = [process_event_task, curate_corpus_task, synthesis_task]
    queues = ['high_priority', 'low_priority']
