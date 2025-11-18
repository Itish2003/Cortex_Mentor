import os
import yaml
import hashlib
from pathlib import Path
from ..models.insights import Insight
from ..models.events import GitCommitEvent, CodeChangeEvent
from ..core.config import Settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    Manages a Zettelkasten-style Knowledge Graph, adopting patterns from
    tools like Obsidian and Dendron for a robust, interconnected system.
    """
    def __init__(self, base_path: str = Settings().knowledge_graph_path):
        self.base_path = Path(base_path)
        (self.base_path / "insights"
       ).mkdir(parents=True, exist_ok=True)
        (self.base_path / "repositories"
       ).mkdir(parents=True, exist_ok=True)

    def _generate_insight_filepath(self, insight: Insight) -> str:
        """
        Generates a unique file name for an insight based on its ID.
        """
        event_type_slug = insight.source_event_type.replace("_", ".").lower()
        if isinstance(insight.source_event, GitCommitEvent):
            short_hash = insight.source_event.commit_hash[:12]
            filename = f"{event_type_slug}.{short_hash}.md"

        elif isinstance(insight.source_event, CodeChangeEvent):
            path_hash = hashlib.md5(insight.source_event.file_path.encode()).hexdigest()[:12]
            timestamp = insight.timestamp.strftime("%Y%m%dT%H%M%S")
            filename = f"{event_type_slug}.{path_hash}.{timestamp}.md"

        else:
            filename = f"generic.{insight.insight_id}.md"

        return filename.replace("/", "_")

    def _create_insight_node(self, insight: Insight) -> Path:
        """
        Creates a markdown representation of an insight with YAML front matter.
        """
        filename = self._generate_insight_filepath(insight)
        # Use the base_path to construct the full, absolute path.
        insight_file = self.base_path / "insights" / filename
        
        repo_name = insight.metadata.get("repo_name")
        parent_repo_node = f"[[../repositories/{repo_name}.md]]" if repo_name else None

        frontmatter = {
            "insight_id": insight.insight_id,
            "source_event_type": insight.source_event_type,
            "timestamp": insight.timestamp.isoformat(),
            "patterns":insight.patterns,
            "parent_nodes": [parent_repo_node] if parent_repo_node else []
        }

        with open(insight_file, "w",encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, sort_keys=False)
            f.write("---\n\n")
            f.write(f"# Insight: {insight.summary}\n\n")

        return insight_file
    
    def _update_index_node(self, index_file: Path, link_to_add: Path):
        """
        Appends a wikilink to an index/hub node.
        """
        # Use os.path.relpath for a more robust relative path calculation
        # that works even when files are in sibling directories.
        relative_link_path = os.path.relpath(link_to_add, start=index_file.parent)
        # os.path.relpath returns a string. We need to ensure it uses forward slashes for the markdown link.
        link_markdown = f"- [[{relative_link_path.replace(os.sep, '/')}]]\n"

        if not index_file.exists():
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(f"# Index: {index_file.stem}\n\n## Related Insights\n\n{link_markdown}")
        else:
            with open(index_file, "a", encoding="utf-8") as f:
                f.write(link_markdown)

    def process_insight(self, insight: Insight):
        """
        Main entry point. Creates an atomic insight node and then updates any relevant index nodes to link to it.
        """
        insight_file_path = self._create_insight_node(insight)
        if isinstance(insight.source_event, GitCommitEvent):
            repo_name = insight.metadata.get("repo_name")
            if repo_name:
                repo_node_path = self.base_path / "repositories" / f"{repo_name}.md"
                self._update_index_node(repo_node_path, insight_file_path)
        
        logger.info(f"Knowledge graph updated. Created insight node: {insight_file_path.name}")