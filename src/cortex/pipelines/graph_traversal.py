from cortex.pipelines.processors import Processor
import logging
import os
import re

logger = logging.getLogger(__name__)

from typing import Optional

class GraphTraversalProcessor(Processor):
    """
    Traverses the knowledge graph to build a rich, multi-hop context.
    """
    def __init__(self, knowledge_graph_root: str):
        self.knowledge_graph_root = knowledge_graph_root

    async def process(self, data: dict, context: dict) -> dict:
        logger.info("Traversing knowledge graph...")
        private_results = data.get("private_results", {})
        documents = private_results.get("documents", [[]])
        if not documents or not documents[0]:
            logger.info("No private results to traverse.")
            data["traversed_knowledge"] = ""
            return data

        entry_points = documents[0]
        traversed_content = []

        for entry_point in entry_points:
            # The entry point from ChromaDB is a full path, we need the relative path
            relative_path = os.path.relpath(entry_point, self.knowledge_graph_root)
            traversed_content.append(self._traverse(relative_path))

        data["traversed_knowledge"] = "\n".join(traversed_content)
        return data

    def _traverse(self, file_path: str, visited: Optional[set] = None) -> str:
        if visited is None:
            visited = set()

        if file_path in visited:
            return ""

        visited.add(file_path)
        full_path = os.path.join(self.knowledge_graph_root, file_path)

        try:
            with open(full_path, "r") as f:
                content = f.read()
        except FileNotFoundError:
            logger.warning(f"File not found during graph traversal: {full_path}")
            return ""

        # Find all [[links]] in the content
        links = re.findall(r"[[(.*?)]]", content)
        traversed_content = [content]

        for link in links:
            # For now, we assume links are file names. A more robust solution
            # would handle different link formats.
            traversed_content.append(self._traverse(link, visited))

        return "\n".join(traversed_content)
