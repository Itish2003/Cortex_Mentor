
import uuid
from cortex.models.events import GitCommitEvent, CodeChangeEvent
from cortex.models.insights import Insight
from cortex.services.llmservice import LLMService

class ComprehensionAgent:
    def __init__(self):
        self.llm_service = LLMService()

    async def process_git_commit_event(self, event: GitCommitEvent) -> Insight:
        """
        Processes a git commit event, generates an AI summary,
        and returns a structured Insight object.
        """
        # 1. Call the LLM service to get a semantic summary
        summary = self.llm_service.generate_commit_summary(
            commit_message=event.message or "",
            commit_diff=event.diff or ""
        )

        # 2. Prepare the content for the vector embedding
        content_for_embedding = (
            f"Commit by {event.author_name} to {event.repo_name}/{event.branch_name}. "
            f"Summary: {summary}. "
            f"Message: {event.message}"
        )

        # 3. Construct the final Insight object
        insight = Insight(
            insight_id=f"commit_{uuid.uuid4().hex[:12]}",
            source_event_type="git_commit",
            summary=summary,
            patterns=[], # We can add pattern detection here in the future
            metadata={
                "repo_name": event.repo_name,
                "branch_name": event.branch_name,
                "commit_hash": event.commit_hash,
            },
            content_for_embedding=content_for_embedding,
            source_event=event
        )
        return insight

    async def process_code_change_event(self, event: CodeChangeEvent) -> Insight:
        """
        Processes a code change event, generates an AI summary,
        and returns a structured Insight object.
        """
        summary = self.llm_service.generate_code_change_summary(
            file_path=event.file_path,
            change_type=event.change_type,
            content=event.content or ""
        )

        content_for_embedding = (
            f"File change in {event.file_path}. "
            f"Type: {event.change_type}. "
            f"Summary: {summary}."
        )

        insight = Insight(
            insight_id=f"code_{uuid.uuid4().hex[:12]}",
            source_event_type="file_change",
            summary=summary,
            patterns=[],
            metadata={
                "file_path": event.file_path,
                "change_type": event.change_type,
            },
            content_for_embedding=content_for_embedding,
            source_event=event
        )
        return insight
