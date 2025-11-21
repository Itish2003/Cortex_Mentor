from cortex.pipelines.processors import Processor
from typing import Any, Dict
from cortex.models.events import SourceEvent, GitCommitEvent,CodeChangeEvent
from cortex.models.insights import Insight
from cortex.services.llmservice import LLMService
from cortex.services.knowledge_graph_service import KnowledgeGraphService
from cortex.services.chroma_service import ChromaService
import logging
from uuid import uuid4
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventDeserializer(Processor):
    """
    Processor to deserialize raw event data into SourceEvent objects.
    """

    async def process(self, data: dict, context: dict) -> SourceEvent:
        event_type = data.get("event_type")
        logger.info(f"Deserializing event of type: {event_type}")
        if event_type == "git_commit":
            event = GitCommitEvent(**data)
        elif event_type == "file_change":
            event = CodeChangeEvent(**data)
        else:
            raise ValueError(f"Unsupported event type: {event_type}")
        
        logger.info(f"Deserialized event of type: {event_type}")
        return event
     
class InsightGenerator(Processor):
    """
    Generates a structured Insight from a source event by calling an LLM.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def process(self, data: SourceEvent, context: dict) -> Insight:
        """
        Takes a source event model and produces an Insight.

        Args:
            data: A validated Pydantic event model (e.g., GitCommitEvent).
            context: The shared context, not used in this processor.

        Returns:
            A new Insight object.
        """
        logger.info(f"Generating insight for event type: {data.event_type}")

        if isinstance(data, GitCommitEvent):
            # Now, use the instance created in __init__
            summary = self.llm_service.generate_commit_summary(
                commit_message=data.message or "",
                commit_diff=data.diff or ""
            )
            content_for_embedding = (
                f"Commit by {data.author_name} to {data.repo_name}/{data.branch_name}. "
                f"Summary: {summary}. "
                f"Message: {data.message}"
            )
            insight = Insight(
                insight_id=f"commit_{uuid4().hex[:12]}",
                source_event_type="git_commit",
                summary=summary,
                patterns=[],
                metadata={
                    "repo_name": data.repo_name,
                    "branch_name": data.branch_name,
                    "commit_hash": data.commit_hash,
                },
                content_for_embedding=content_for_embedding,
                source_event=data
            )
            return insight

        elif isinstance(data, CodeChangeEvent):
            summary = self.llm_service.generate_code_change_summary(
                file_path=data.file_path,
                change_type=data.change_type,
                content=data.content or ""
            )

            content_for_embedding = (
                f"File change in {data.file_path}. "
                f"Type: {data.change_type}. "
                f"Summary: {summary}."
            )

            insight = Insight(
                insight_id=f"code_{uuid4().hex[:12]}",
                source_event_type="file_change",
                summary=summary,
                patterns=[],
                metadata={
                    "file_path": data.file_path,
                    "change_type": data.change_type,
                },
                content_for_embedding=content_for_embedding,
                source_event=data
            )
            return insight
        
        raise TypeError(f"Unsupported event type for insight generation: {type(data)}")
    
class KnowledgeGraphWriter(Processor):
    """
    Processor to write Insights to the knowledge graph.
    """
    def __init__(self, kg_service: KnowledgeGraphService):
        self.kg_service = kg_service

    async def process(self, data: Insight, context: dict) -> None:
        logger.info(f"Writing insight {data.insight_id} to knowledge graph.")
        self.kg_service.process_insight(data)
        logger.info(f"Insight {data.insight_id} written to knowledge graph.")
        return None
    
class ChromaWriter(Processor):
    """
    Processor to write Insights to the Chroma vector database.
    """
    def __init__(self, chroma_service: ChromaService):
        self.chroma_service = chroma_service

    async def process(self, data: Insight, context: dict) -> None:
        logger.info(f"Adding insight {data.insight_id} to ChromaDB.")
        self.chroma_service.add_document(
            doc_id=data.insight_id,
            content=data.content_for_embedding,
            metadata=data.metadata
        )
        logger.info(f"Insight {data.insight_id} added to ChromaDB.")
        return None

class SynthesisTrigger(Processor):
    """
    Processor to trigger synthesis tasks based on the generated Insight.
    """
    async def process(self, data: Insight, context: dict) -> None:
        logger.info(f"Triggering synthesis task for insight {data.insight_id}.")
        redis = context.get("redis")
        if data and redis:
            logger.info(f"Enqueuing synthesis task for insight {data.insight_id}.")
            await redis.enqueue_job('synthesis_task', data.content_for_embedding)
        elif not redis:
            logger.error("Redis pool not found in context for SynthesisTrigger.")
        logger.info(f"Synthesis task triggered for insight {data.insight_id}.")
        return None