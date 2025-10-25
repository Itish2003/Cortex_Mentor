# Vision Realisation: Current State vs. Architectural Dream

This document outlines the current implementation status of the Cortex Mentor project in relation to the high-level vision described in `architecture.md`. It serves as a "current reality" check to guide future development.

## The Vision: A Smart, Linked Knowledge Graph

The core architectural vision is to use a structured, interlinked Markdown knowledge graph (a "Zettelkasten") to build a precise, low-bloat context for the LLM.

The key idea is to move beyond simple semantic search and leverage the *relationships* between pieces of information. By traversing the graph, the system can assemble a highly relevant, multi-hop context, which is far more powerful than just finding disconnected, semantically similar text chunks.

## The Reality: A Foundation Built, But Not Fully Utilized

The project has successfully laid the essential foundation for this vision, but does not yet fully capitalize on it during the knowledge retrieval phase.

### What We Are Doing Now (The Foundation)

- ✅ **Dual-Write System**: The `ComprehensionPipeline` correctly performs a "dual write":
    1.  It saves structured, human-readable insights to the Markdown knowledge graph using the `KnowledgeGraphWriter`.
    2.  It saves machine-searchable vector embeddings to a local ChromaDB instance using the `ChromaWriter`.
- ✅ **Graph Structure Creation**: We are successfully creating the *nodes* of our knowledge graph as individual Markdown files.

### The Gap: Where We Are Falling Short

- ❌ **Retrieval is Vector-Only**: The `SynthesisPipeline` currently relies exclusively on the `PrivateKnowledgeQuerier`, which uses `ChromaService` for semantic vector search.
- ❌ **Graph Links Are Not Traversed**: The system finds "entry-point" documents based on semantic similarity but **does not traverse the links** within those Markdown files to gather deeper, relational context.

**In summary, we are currently *writing* a graph, but we are *reading* from a simple list.** The "build the right context" step of the vision is not yet implemented; we are still just "finding similar context."

## Next Steps: Realising the Vision

To bridge this gap and fully realize the vision, we have implemented a knowledge augmentation strategy that uses a gateway agent to decide when to trigger a curation pipeline for web search and knowledge base augmentation.

- **Implemented Enhancement**: We have created a `KnowledgeGatewayProcessor` that uses an LLM agent to decide if the public knowledge is sufficient. If not, it triggers a `CurationProcessor` that uses a sequential agent to search the web and add new information to the public knowledge base. The `PrivateKnowledgeQuerier` and `PublicKnowledgeQuerier` now run in parallel to improve performance.
- **Logic**:
    1.  The `KnowledgeGatewayProcessor` evaluates the public knowledge and makes a boolean decision: `needs_improvement`.
    2.  If `needs_improvement` is `True`, the `CurationTriggerProcessor` triggers the `CurationProcessor`.
    3.  The `CurationProcessor` runs a sequential agent that first uses `google_search` to find relevant information, then uses a `relevance_judge` agent to decide what to write to the Upstash knowledge base.
    4.  The augmented knowledge is then passed to the `InsightSynthesizer`.

While this improves the quality of the knowledge base, the core goal of traversing the local knowledge graph is still not yet implemented. The next logical step is to enhance our knowledge retrieval process to do so.

- **Proposed Enhancement**: Update the `PrivateKnowledgeQuerier` or create a new `GraphTraversalProcessor`.
- **Logic**:
    1.  Use ChromaDB to get the initial, most relevant "entry point" nodes in the graph.
    2.  Parse the corresponding Markdown files for those nodes.
    3.  **Traverse the `[[links]]`** within those files to discover and fetch content from directly related nodes.
    4.  Assemble this rich, multi-hop context to be sent to the LLM for synthesis.

By implementing this graph traversal logic, we will move from a simple RAG system to a true Knowledge Graph-based reasoning system, fully realizing the initial architectural dream.
