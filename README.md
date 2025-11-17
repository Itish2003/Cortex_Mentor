# Cortex Mentor: An AI-Powered Software Development Mentor

Cortex Mentor is an advanced, event-driven, and privacy-focused AI assistant designed to accelerate software development. It acts as a persistent, personalized mentor that observes a developer's workflow, understands the context behind their actions, and provides intelligent, real-time audio insights.

This repository contains the **backend services** for Cortex Mentor. The frontend client is a VS Code extension located in the `cortex-vs` directory.

At its core, Cortex Mentor is built on a **Hybrid Knowledge Model**, combining a private, local-first knowledge graph with a public, cloud-based knowledge base. This ensures that all user-specific data remains secure and private on the local machine, while still allowing the system to leverage powerful cloud-based models and curated expert knowledge.

## Key Architectural Pillars

- **Pipeline-Based Architecture**: The system is built on a modular and scalable pipeline architecture. Each stage of the process, from understanding raw events to synthesizing complex insights, is handled by a series of self-contained, reusable "Processors."

- **Parallel Processing**: For maximum efficiency, the synthesis pipeline runs independent sub-pipelines in parallel. It concurrently queries and traverses the private knowledge graph while also querying and augmenting the public knowledge base, significantly reducing latency.

- **Multi-Agent System**: Cortex Mentor uses a sophisticated, multi-agent system (powered by the Google ADK framework) for complex reasoning and data augmentation. This includes a sequential pipeline of agents that can perform web searches, analyze results from multiple perspectives, and synthesize new knowledge.

- **Hybrid Knowledge Stores**:
    - **Private Knowledge Graph (Zettelkasten & VectorDB)**: A local-first system where a developer's activity is recorded in a human-readable, interlinked Markdown knowledge graph. This is supplemented by a local ChromaDB vector store for fast semantic search, with all embeddings generated locally via Ollama to ensure privacy.
    - **Public Knowledge Base**: A cloud-based Upstash vector database containing curated, high-quality software development knowledge, which can be intelligently and automatically augmented over time.

- **Hybrid LLM Strategy**: The system intelligently uses different LLMs for different tasks. It leverages local Ollama models for processing private, sensitive data, and powerful cloud-based Gemini models (2.5 Pro and 2.5 Flash) for tasks requiring vast world knowledge and complex reasoning, such as web search analysis and final insight synthesis.

- **Real-time Audio Delivery**: The system delivers insights as real-time audio streams using Google's Text-to-Speech API, WebSockets, and a Redis Pub/Sub message bus for a seamless, ambient user experience.

- **Local-First & Private**: All user-specific data, including source code, commit messages, and the private knowledge graph, remains on the local machine. Privacy is a foundational principle of the architecture.

## Project Structure
- `src/cortex/main.py`: FastAPI app serving as the API gateway and WebSocket server.
- `src/cortex/workers.py`: ARQ worker definitions for background task processing.
- `src/cortex/api/events.py`: API endpoint for event ingestion.
- `src/cortex/pipelines/`: The modular Pipeline & Processor architecture.
- `src/cortex/services/`: Services for interacting with ChromaDB, Ollama, and other external APIs.
- `src/cortex/models/`: Pydantic models for events and insights.
- `observers/`: Scripts for observing the developer environment (e.g., Git post-commit hook).

## Usage

### 1. Install Dependencies
This project uses `uv` for package management.
```zsh
# This will create a .venv and install packages from pyproject.toml
uv pip install -e .
```

### 2. Set Up Environment Variables
Create a `.env` file in the root of the `cortex_mentor` directory and add your API keys:
```
UPSTASH_URL="your_upstash_vector_db_url"
UPSTASH_TOKEN="your_upstash_vector_db_token"
GEMINI_API_KEY="your_google_ai_studio_api_key"
```

### 3. Run Local Infrastructure
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

### 4. Run the Backend
The backend consists of two main processes: the API server and the background worker.

**Terminal 3: Start the ARQ Worker**
This process listens for and executes background jobs like processing events and synthesizing insights.
```zsh
uv run arq src.cortex.workers.WorkerSettings
```

**Terminal 4: Start the FastAPI Server**
This process handles incoming API requests and manages the WebSocket connections for real-time delivery.
```zsh
uv run uvicorn src.cortex.main:app --reload
```

### 5. Run the Frontend
See the `README.md` file in the `cortex-vs` directory for instructions on how to run the VS Code extension.

---
For more architectural details, see the documentation in `docs/`.
