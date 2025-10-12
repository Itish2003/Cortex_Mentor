# Cortex Mentor: An AI-Powered Software Development Mentor

Cortex Mentor is an event-driven, agentic framework designed to observe a developer's workflow, build a private knowledge graph of their activities, and provide intelligent insights and guidance. It uses a local-first RAG (Retrieval-Augmented Generation) architecture, ensuring user privacy while leveraging powerful local AI models.

## Features
- **Event-Driven Architecture**: Ingests events from various observers (Git hooks, file watchers, etc.) via a FastAPI gateway.
- **Asynchronous Task Processing**: Uses ARQ and Redis to manage a robust background task queue for processing events without blocking.
- **AI Agent Fleet**: A multi-level agent system (`ComprehensionAgent`, `SynthesisAgent`, etc.) processes raw data into structured insights.
- **Hybrid Knowledge Store**: 
    - **Markdown Zettelkasten**: Human-readable logs of all insights are stored in local markdown files.
    - **Vector Search Index**: ChromaDB and local Ollama embeddings power a searchable index over the knowledge graph for fast, semantic retrieval.
- **Local First & Private**: All user data, models, and services run entirely on the local machine, guaranteeing privacy.

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
