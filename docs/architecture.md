
# Cortex Mentor Architecture

This document outlines the architecture of the Cortex Mentor application, a system designed to analyze software development events and provide intelligent insights.

## 1. High-Level Architecture

The Cortex Mentor application is built on a **Hybrid Knowledge Model**, which separates private user data from a public, curated knowledge base. This ensures user privacy while leveraging a powerful cloud-based platform for expert knowledge. The architecture is event-driven and uses a multi-agent system to process and analyze development data.

The core components are:

- **Event-Driven API**: A FastAPI-based API receives events from observers like IDE plugins and Git hooks.
- **Asynchronous Task Queue**: ARQ and Redis manage background jobs for event processing.
- **Hybrid Knowledge Stores**:
    - **Private User Model (Zettelkasten & Search Index)**: This is a dual-component system for storing user-specific data securely on the user's machine.
        - **Markdown Files (Source of Truth)**: The `data/knowledge_graph/` directory contains interlinked markdown files that form the primary, human-readable, and persistent memory of the mentor's understanding of the user (the "Zettelkasten").
        - **ChromaDB (Search Index)**: A local ChromaDB instance acts as a performance layer, storing vector embeddings of the markdown content. It serves as a high-speed, machine-readable search index, with metadata pointing back to the source markdown files.
    - **Public MCP Knowledge Base**: A cloud-based Upstash Context platform containing curated, high-quality software development knowledge.
- **AI Agent Fleet**:
    - **Level 1 (Comprehension)**: Processes raw events and stores insights in the private user model.
    - **Level 2 (Synthesis)**: Combines insights from both the private user model and the public MCP knowledge base to provide expert advice.
    - **Corpus Curator**: A background agent responsible for populating and maintaining the public MCP knowledge base.
- **Observers**: A collection of local tools that monitor file changes, Git hooks, and IDE events.

The following diagram illustrates the Hybrid Knowledge Model architecture:

```mermaid
graph TD
    %% ===================================================
    %% 1. DEFINE ALL NODES & SUBGRAPHS FIRST
    %% ===================================================

    subgraph "User's Local Machine"
        subgraph "Environment (Observers)"
            A[IDE Plugin]
            B[Git Hooks]
            C[CLI Wrapper]
        end
        
        subgraph "Private RAG System (User Model)"
            F["<b style='font-size:14px'>Markdown Knowledge Graph</b><br/><i>(The Human-Readable Source)</i>"]
            G["<b>Local ChromaDB</b><br/><i>(The Searchable Index)</i>"]
            H["<b>Local Ollama</b><br/><i>(The Private Embedding Engine)</i>"]
        end
    end

    subgraph "Cortex Backend (Server / Cloud)"
        subgraph "Ingestion & Task Management"
            D[FastAPI Gateway]
            E["<b>ARQ Task Queue</b><br/><i>(Managed by Redis)</i>"]
        end
        
        subgraph "Agent Fleet (Persistent ARQ Workers)"
            AGENT_L1["<b>L1: Comprehension Agent</b><br/><i>Analyzes Raw Events</i>"]
            AGENT_L2["<b>L2: Synthesis & Strategy Agent</b><br/><i>Forms Opinions & Plans</i>"]
            AGENT_L3["<b>L3: Engagement & Guidance Agent</b><br/><i>Crafts User-Facing Messages</i>"]
            AGENT_CURATOR["<b>Corpus Curator Agent</b><br/><i>(Background Librarian)</i>"]
        end
        
        subgraph "Public RAG System (MCP)"
            I["<b>Upstash Context Platform</b><br/><i>The Expert Knowledge Library</i>"]
        end
    end

    %% ===================================================
    %% 2. DEFINE STYLES
    %% ===================================================

    style A fill:#D6EAF8,stroke:#3498DB
    style B fill:#D6EAF8,stroke:#3498DB
    style C fill:#D6EAF8,stroke:#3498DB
    style F fill:#FADBD8,stroke:#C0392B,color:#000
    style G fill:#FDEDEC,stroke:#C0392B,color:#000
    style I fill:#D5F5E3,stroke:#2ECC71,color:#000

    %% ===================================================
    %% 3. DEFINE ALL LINKS & DATA FLOWS LAST
    %% ===================================================

    %% ---> Flow 1: Ingestion
    A -- "1. Raw Event" --> D
    B -- "1. Raw Event" --> D
    C -- "1. Raw Event" --> D
    D -- "2. Enqueues Job" --> E
    
    %% ---> Flow 2: Level 1 Comprehension (Building the User Model)
    E -- "3. Dispatches Job" --> AGENT_L1
    AGENT_L1 -- "4a. Writes to<br/>Human-Readable Source" --> F
    AGENT_L1 -- "4b. Updates<br/>Searchable Index" --> G
    G -- "Embedded via" --> H
    
    %% ---> Flow 3: Level 2 Synthesis (The "Thinking" Step)
    AGENT_L1 -- "5. Enqueues<br/>Synthesis Task" --> E
    E -- "6. Dispatches Job" --> AGENT_L2
    AGENT_L2 -- "7a. Queries<br/>User History" --> G
    AGENT_L2 -- "7b. Queries<br/>Expert Knowledge" --> I
    
    %% ---> Flow 4: Level 3 Engagement (Delivering Guidance)
    AGENT_L2 -- "8. Enqueues<br/>Guidance Task" --> E
    E -- "9. Dispatches Job" --> AGENT_L3
    AGENT_L3 -- "10. Delivers<br/>Guidance" --> A
    
    %% ---> Flow 5: Knowledge Curation (Parallel Background Process)
    AGENT_CURATOR -- "Curates & Populates<br/>the Mentor's Library" --> I
```

## 2. Infrastructure

The application is designed for containerized deployment using Docker, ensuring a consistent environment for development and production. The key infrastructure components are:

- **API Server (FastAPI & Uvicorn)**: A high-performance Uvicorn server runs the FastAPI application. FastAPI was chosen for its modern features, asynchronous capabilities, automatic data validation with Pydantic, and interactive API documentation. It serves as the primary entry point for all incoming events.

- **Asynchronous Task Queue (ARQ & Redis)**: ARQ is used for its simplicity, high performance, and native `asyncio` support. It manages background tasks like event processing and knowledge curation. Redis acts as the message broker for ARQ, providing a robust and scalable foundation for the task queue.

- **Private Knowledge Store (ChromaDB & Ollama)**:
    - **ChromaDB**: A local, persistent ChromaDB instance is used as the vector store for the private user model. It was chosen for its ease of use, file-based storage, and efficient semantic search capabilities, making it ideal for running on a user's local machine.
    - **Ollama**: Ollama provides local access to large language models (like `nomic-embed-text`) for generating text embeddings. This allows all user data and embeddings to remain entirely on the user's machine, ensuring maximum privacy.

- **Public Knowledge Store (Upstash)**: Upstash is a serverless data platform that provides a managed vector database. It was chosen for the public MCP Knowledge Base due to its scalability, ease of use, and pay-as-you-go pricing, making it a cost-effective solution for storing and querying curated, expert knowledge.

- **CI/CD (GitHub Actions)**: The `.github/workflows/python-app.yml` file defines a continuous integration pipeline using GitHub Actions. This pipeline automates the process of installing dependencies, running tests, and linting the codebase on every push, ensuring code quality and stability.

## 3. Code Details

The application's code is organized into a modular structure within the `src/cortex` directory, promoting separation of concerns and maintainability.

- **`main.py`**: The main entry point of the FastAPI application. It initializes the app, sets up the lifespan events (like creating the Redis pool), and includes the API routers.

- **`api/events.py`**: Defines the API endpoints for receiving events. It handles incoming HTTP requests, validates the event data using Pydantic models, and enqueues the events as jobs in the ARQ task queue.

- **`workers.py`**: Configures the ARQ worker settings. It defines the tasks that the workers can execute (e.g., `process_event_task`, `curate_corpus_task`) and maps them to specific queues (e.g., `high_priority`, `low_priority`).

- **`core/`**: Contains the core application logic and configuration.
    - `config.py`: Manages application settings using Pydantic's `BaseSettings`, allowing for configuration via environment variables.
    - `redis.py`: Handles the creation and lifecycle of the Redis connection pool for the ARQ task queue.

- **`models/events.py`**: Defines the Pydantic models for the event data structures, ensuring that all incoming data is well-formed and validated.

- **`services/`**: Contains the service classes that provide an abstraction layer for interacting with external data stores.
    - `chroma_service.py`: Manages all interactions with the local ChromaDB instance, including adding documents and querying for similar insights.
    - `upstash_service.py`: Manages all interactions with the Upstash Vector DB, handling the public MCP Knowledge Base.

- **`agents/`**: Contains the AI agents that perform the core logic of the application.
    - `level1_comprehension.py`: The Level 1 agent processes raw events, generates human-readable insights, and performs the dual-write to the Markdown Knowledge Graph and the ChromaDB index.
    - `level2_synthesis.py`: The Level 2 agent queries both the private and public knowledge stores to synthesize higher-level insights and form expert opinions.
    - `level3_curation/corpus_curator.py`: The Corpus Curator agent is responsible for curating and populating the public MCP Knowledge Base in the background.

## 4. Data Flow

The following steps outline the lifecycle of an event within the Cortex Mentor application:

1.  **Event Ingestion**: An observer (e.g., an IDE plugin or Git hook) sends a raw event to the FastAPI API Gateway.

2.  **Task Queuing**: The API gateway validates the event and enqueues it as a job in the `high_priority` ARQ task queue.

3.  **Level 1 Comprehension**: An ARQ worker picks up the job and dispatches it to the **Level 1 Comprehension Agent**.

4.  **Dual-Write to Private Model**: The L1 Agent processes the event and performs two actions:
    a.  It appends a human-readable insight to the appropriate Markdown file in the `data/knowledge_graph/` directory (the source of truth).
    b.  It simultaneously updates the local ChromaDB instance with the vector embedding of the insight, including a metadata pointer back to the source Markdown file.

5.  **Level 2 Synthesis (Optional)**: After processing, the L1 Agent can enqueue a follow-up job for the **Level 2 Synthesis Agent** if a deeper analysis is required.

6.  **Insight Synthesis**: The L2 Agent queries both the private user model (ChromaDB) and the public MCP knowledge base (Upstash) to form a holistic understanding and generate expert advice.

7.  **Corpus Curation (Parallel)**: Independently, the **Corpus Curator Agent** runs as a background task on a `low_priority` queue, curating and populating the Upstash MCP with high-quality data.
