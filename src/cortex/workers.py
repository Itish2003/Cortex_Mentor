
from cortex.models.insights import Insight
import logging
from cortex.core.redis import create_redis_pool, close_redis_pool
from cortex.pipelines.pipelines import Pipeline
from cortex.pipelines.comprehension import (
    EventDeserializer,
    InsightGenerator,
    KnowledgeGraphWriter,
    ChromaWriter,
    SynthesisTrigger
)
from cortex.pipelines.synthesis import create_synthesis_pipeline
from cortex.services.knowledge_graph_service import KnowledgeGraphService
from cortex.services.chroma_service import ChromaService
from cortex.services.upstash_service import UpstashService
from cortex.core.config import Settings
from cortex.pipelines.graph_traversal import GraphTraversalProcessor
from cortex.services.llmservice import LLMService
from google.adk.tools import google_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event_task(ctx, event_data: dict):
    """
    ARQ task to process a raw event using the new pipeline architecture.
    """
    logger.info(f"--- Starting Comprehension Pipeline for Event ---")

    # 1. Instantiate services that the processors will need.
    kg_service = KnowledgeGraphService()
    chroma_service = ChromaService()
    llm_service = LLMService()

    # 2. Define the pipeline by injecting dependencies into the processors.
    comprehension_pipeline = Pipeline([
        EventDeserializer(),
        InsightGenerator(llm_service=llm_service),
        [
            KnowledgeGraphWriter(kg_service),
            ChromaWriter(chroma_service),
        ],
        SynthesisTrigger(),
    ])

    # 3. The context now only holds run-specific objects like the redis pool.
    context = {
        "redis": ctx.get("redis")
    }

    try:
        await comprehension_pipeline.execute(
            data=event_data,
            context=context
        )
        logger.info(f"--- Comprehension Pipeline Finished Successfully ---")

    except Exception as e:
        logger.error(f"Comprehension pipeline failed: {e}", exc_info=True)

async def on_startup(ctx):
    """
    Creates the redis pool on worker startup and stores it in the context.
    """
    ctx["redis"] = await create_redis_pool()

async def on_shutdown(ctx):
    """
    Closes the redis pool on worker shutdown.
    """
    await close_redis_pool(ctx.get("redis"))

async def synthesis_task(ctx, query_text: str):
    """
    ARQ task to perform synthesis on the given query text.
    """
    logger.info(f"--- Starting Synthesis Pipeline for Query: {query_text[:50]}... ---")

    # 1. Instantiate services.
    chroma_service = ChromaService()
    upstash_service = UpstashService()
    llm_service = LLMService()

    # 2. Define the pipeline.
    synthesis_pipeline = create_synthesis_pipeline(chroma_service, upstash_service, llm_service)

    context = {
        "redis": ctx.get("redis"),
        "google_search": google_search
    }

    try:
        await synthesis_pipeline.execute(
            data=query_text,
            context=context
        )
        logger.info(f"--- Synthesis Pipeline Finished Successfully ---")
    except Exception as e:
        logger.error(f"Synthesis pipeline failed: {e}", exc_info=True)

class WorkerSettings:
    functions = [process_event_task, synthesis_task]
    queues = ['high_priority', 'low_priority']
    on_startup = on_startup
    on_shutdown = on_shutdown