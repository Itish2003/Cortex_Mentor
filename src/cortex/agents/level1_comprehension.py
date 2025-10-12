
import os
from cortex.core.config import Settings
from typing import Dict, Any
from cortex.models.events import GitCommitEvent, CodeChangeEvent
from datetime import datetime
from typing import List, Tuple

class ComprehensionAgent:
    def __init__(self):
        self.settings = Settings()
        os.makedirs(self.settings.knowledge_graph_path, exist_ok=True)

    async def process_git_commit_event(self, event_data:GitCommitEvent) -> Dict[str, Any]:
        """
        Processes a git commit event, appends it to the markdown knowledge graph,
        and prepares it for ChromaDB indexing.
        """
        title = "Git Commit"
        details = [
            ("Repo/Branch", f"`{event_data.repo_name}/{event_data.branch_name}`"),
            ("Author", f"`{event_data.author_name}`"),
            ("Message", event_data.message.strip() if event_data.message else "No commit message"),
            ("Commit", f"`{event_data.commit_hash[:7]}`"),
        ]

        if event_data.stats:
            stats_str = f"{event_data.stats.get('files_changed', 0)} files changed ({event_data.stats.get(
      'insertions', 0)} insertions, {event_data.stats.get('deletions', 0)} deletions)."
            details.append(("Changes", stats_str))

        insight = self._generate_insight(title,event_data.timestamp,details)
        self._append_to_log(insight,"git_log.md")
        
        return {
            "id": event_data.commit_hash,
            "content":insight,
            "metadata":{
                "source":"git_commit",
                "timestamp": event_data.timestamp.isoformat(),
                "repo_name": event_data.repo_name,
                "author": event_data.author_name,
                "branch": event_data.branch_name
            }
        }

    async def process_code_change_event(self, event_data: CodeChangeEvent) -> Dict[str, Any]:
        """
        Processes a code change event, appends it to the markdown knowledge graph,
        and prepares it for ChromaDB indexing.
        """
        title = "File Change"
        details = [
            ("File", f"`{event_data.file_path}`"),
            ("Change", f"The file was **{event_data.change_type}**."),
        ]

        insight = self._generate_insight(title, event_data.timestamp, details)
        self._append_to_log(insight, "file_change_log.md")

        event_id = f"{event_data.file_path}@{event_data.timestamp.isoformat()}"

        return {
            "id": event_id,
            "content": insight,
            "metadata": { "source": "file_change", "timestamp": event_data.timestamp.isoformat(), "file_path":
      event_data.file_path }
        }

    def _generate_insight(self, title: str, timestamp: datetime, details: List[Tuple[str, Any]]) -> str:
            """
            Generates a standardized, human-readable insight from a title and a list of details.
            """
            # Use flexible type casting for detail values
            details_str = "\n".join(f"- **{key}**: {str(value)}" for key, value in details)

            insight_text = f"""
---
### {title} on {timestamp.strftime('%Y-%m-%d %H:%M')}
{details_str}
"""
            return insight_text

    def _append_to_log(self, insight: str, filename: str):
        """Appends the insight to a specified markdown log file."""
        file_path = os.path.join(self.settings.knowledge_graph_path, filename)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{insight}")
