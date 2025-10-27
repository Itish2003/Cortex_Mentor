# Cortex Mentor: An AI-Powered Software Development Mentor

Cortex Mentor is an advanced, event-driven, and privacy-focused AI assistant designed to accelerate software development. It acts as a persistent, personalized mentor that observes a developer's workflow, understands the context behind their actions, and provides intelligent, timely insights.

At its core, Cortex Mentor is built on a **Hybrid Knowledge Model**, combining a private, local-first knowledge graph with a public, cloud-based knowledge base. This ensures that all user-specific data remains secure and private on the local machine, while still allowing the system to leverage powerful cloud-based models and curated expert knowledge.

## Key Architectural Pillars

- **Pipeline-Based Architecture**: The system is built on a modular and scalable pipeline architecture. Each stage of the process, from understanding raw events to synthesizing complex insights, is handled by a series of self-contained, reusable "Processors."

- **Parallel Processing**: For maximum efficiency, the synthesis pipeline runs independent sub-pipelines in parallel. It concurrently queries and traverses the private knowledge graph while also querying and augmenting the public knowledge base, significantly reducing latency.

- **Multi-Agent System**: Cortex Mentor uses a sophisticated, multi-agent system (powered by the Google ADK framework) for complex reasoning and data augmentation. This includes a sequential pipeline of agents that can perform web searches, analyze results from multiple perspectives, and synthesize new knowledge.

- **Hybrid Knowledge Stores**:
    - **Private Knowledge Graph (Zettelkasten & VectorDB)**: A local-first system where a developer's activity is recorded in a human-readable, interlinked Markdown knowledge graph. This is supplemented by a local ChromaDB vector store for fast semantic search, with all embeddings generated locally via Ollama to ensure privacy.
    - **Public Knowledge Base**: A cloud-based Upstash vector database containing curated, high-quality software development knowledge, which can be intelligently and automatically augmented over time.

- **Hybrid LLM Strategy**: The system intelligently uses different LLMs for different tasks. It leverages local Ollama models for processing private, sensitive data, and powerful cloud-based Gemini models (2.5 Pro and 2.5 Flash) for tasks requiring vast world knowledge and complex reasoning, such as web search analysis and final insight synthesis.

- **Local-First & Private**: All user-specific data, including source code, commit messages, and the private knowledge graph, remains on the local machine. Privacy is a foundational principle of the architecture.

## Project Structure
- `src/cortex/main.py`: FastAPI app serving as the API gateway.
- `src/cortex/workers.py`: ARQ worker definitions for background task processing.
- `src/cortex/api/events.py`: API endpoint for event ingestion.
- `src/cortex/agents/`: The AI agents responsible for data processing and insight generation.
- `src/cortex/services/`: Services for interacting with ChromaDB, Ollama, and the Knowledge Graph.
- `src/cortex/models/`: Pydantic models for events and insights.
- `src/cortex/services/knowledge_graph_service.py`: Manages the Zettelkasten-style markdown knowledge graph.
- `src/cortex/services/llmservice.py`: Service for interacting with local LLMs for summary generation.
- `src/cortex/models/insights.py`: Pydantic models defining the structure of processed insights.
- `observers/`: Scripts for observing the developer environment (e.g., Git post-commit hook).

## Usage

### 1. Install Dependencies
This project uses `uv` for package management.
```zsh
# This will create a .venv and install packages from pyproject.toml
uv pip install -e .
```

### 2. Run Local Infrastructure
In separate terminals, start the required services:

**Terminal 1: Start Redis**
(If you installed with Homebrew and it's not already running)
```zsh
brew services start redis
```

**Terminal 2: Start Ollama & Pull Models**
Make sure the Ollama application is running. Then, pull the required models:
```zsh
# For embeddings
ollama pull nomic-embed-text:v1.5

# For summary generation
ollama pull llava-llama3:latest
```

**Terminal 3: Start the ARQ Worker**
```zsh
uv run arq src.cortex.workers.WorkerSettings
```

### 3. Run the FastAPI Server

**Terminal 4: Start the API Gateway**
```zsh
uv run uvicorn src.cortex.main:app --reload
```

### 4. Configure and Trigger an Event

**Terminal 5: Configure and make a git commit**
First, tell the git hook where the API is running:
```zsh
git config --local cortex.api-url "http://127.0.0.1:8000/api/events"
```
Now, make a commit to trigger the pipeline:
```zsh
touch test_file.txt
git add .
git commit -m "Test: Triggering the Cortex observer pipeline"
```
Watch the ARQ worker and Uvicorn terminals for activity.

---
For more architectural details, see the documentation in `docs/`.
