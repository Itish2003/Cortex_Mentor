# Cortex Mentor Architecture

This document outlines the architecture of the Cortex Mentor application, a system designed to analyze software development events and provide intelligent insights.

## 1. High-Level Architecture

The Cortex Mentor application is built on a **Hybrid Knowledge Model**, which separates private user data from a public, curated knowledge base. This ensures user privacy while leveraging a powerful cloud-based platform for expert knowledge. The architecture is event-driven and uses a multi-agent system to process and analyze development data.

The core components are:

- **Event-Driven API**: A FastAPI-based API receives events from observers like IDE plugins and Git hooks, and also manages WebSocket connections for real-time insight delivery.
- **Asynchronous Task Queue**: ARQ and Redis manage background jobs for event processing, with workers publishing insights to Redis Pub/Sub for real-time delivery.
- **Hybrid Knowledge Stores**:
  - **Private User Model (Zettelkasten & Search Index)**: This is a dual-component system for storing user-specific data securely on the user's machine.
    - **Markdown Files (Source of Truth)**: The `data/knowledge_graph/` directory contains interlinked markdown files that form the primary, human-readable, and persistent memory of the mentor's understanding of the user (the "Zettelkasten").
    - **ChromaDB (Search Index)**: A local ChromaDB instance acts as a performance layer, storing vector embeddings of the markdown content. It serves as a high-speed, machine-readable search index, with metadata pointing back to the source markdown files.
  - **Public MCP Knowledge Base**: A cloud-based Upstash Context platform containing curated, high-quality software development knowledge.
- **Processing Pipelines**:
  - **Level 1 (Comprehension Pipeline)**: Processes raw events and stores insights in the private user model.
  - **Level 2 (Synthesis Pipeline)**: Combines insights from both the private user model and the public MCP knowledge base to provide expert advice.
  - **Level 3 (Delivery Pipeline)**: The `AudioDeliveryProcessor` uses Gemini TTS to convert synthesized insights into audio and delivers them in real-time.
  - **Curation Pipeline**: A background pipeline responsible for populating and maintaining the public MCP knowledge base.
- **Observers**: A collection of local tools that monitor file changes, Git hooks, and IDE events.
- **Real-time Communication**: WebSockets for client-server communication and Redis Pub/Sub as a message bus between background workers and the FastAPI server.
- **AI Services**: Integration with Google Gemini models, including Gemini TTS for advanced audio synthesis.

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
        User([User])
    end

    subgraph "Cortex Backend (Server / Cloud)"
        subgraph "Real-time Delivery & Task Management"
            D[FastAPI Gateway]
            D1(WebSocket Connections)
            D2[Redis Pub/Sub]
            E["<b>ARQ Task Queue</b><br/><i>(Managed by Redis)</i>"]
        end

        subgraph "Processing Pipelines (Persistent ARQ Workers)"
            AGENT_L1["<b>L1: Comprehension Pipeline</b><br/><i>Analyzes Raw Events</i>"]
            AGENT_L2["<b>L2: Synthesis Pipeline</b><br/><i>Forms Opinions & Plans</i>"]
            AGENT_L3["<b>L3: Delivery Pipeline</b><br/><i>(AudioDeliveryProcessor)</i>"]
            AGENT_CURATOR["<b>Curation Pipeline</b><br/><i>(Background Librarian)</i>"]
        end

        subgraph "Public RAG System (MCP)"
            I["<b>Upstash Context Platform</b><br/><i>The Expert Knowledge Library</i>"]
            J[Gemini TTS]
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
    style J fill:#D5F5E3,stroke:#2ECC71,color:#000
    style User fill:#FADBD8,stroke:#C0392B

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
    AGENT_L2 -- "7a. Queries / Gets Results" --- G
    AGENT_L2 -- "7b. Queries / Gets Results" --- I

    %% ---> Flow 4: Level 3 Engagement (Delivering Guidance)
    AGENT_L2 -- "8. Enqueues<br/>Delivery Task" --> E
    E -- "9. Dispatches Job" --> AGENT_L3
    AGENT_L3 -- "10. Generates Audio via" --> J
    AGENT_L3 -- "11. Publishes Audio to" --> D2
    D -- "12. Broadcasts Audio via" --> D1
    D1 -- "13. Delivers to" --> A
    A -- "14. Presents to" --> User

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

- **Real-time Communication (WebSockets & Redis Pub/Sub)**: To deliver insights to the user in real-time, the system uses a WebSocket connection managed by the FastAPI server. Background workers producing insights publish them to a Redis Pub/Sub channel, which the FastAPI server subscribes to, broadcasting the messages to all connected clients.

- **AI Services (Gemini & Ollama)**: The application leverages a hybrid model strategy, using local Ollama models for privacy-sensitive tasks and powerful Google Gemini models (including Gemini TTS for audio synthesis) for advanced reasoning and content generation.

- **CI/CD (GitHub Actions)**: The `.github/workflows/python-app.yml` file defines a continuous integration pipeline using GitHub Actions. This pipeline automates the process of installing dependencies, running tests, and linting the codebase on every push, ensuring code quality and stability.

## 3. Code Details

The application's code is organized into a modular structure within the `src/cortex` directory, promoting separation of concerns and maintainability.

- **`main.py`**: The main entry point of the FastAPI application. It initializes the app, sets up lifespan events (like creating the Redis pool), includes API routers, and manages WebSocket connections for real-time insight delivery.

- **`api/events.py`**: Defines the API endpoints for receiving events. It handles incoming HTTP requests, validates the event data using Pydantic models, and enqueues the events as jobs in the ARQ task queue.

  - **`workers.py`**: Configures the ARQ worker settings. It defines the tasks that the workers can execute (e.g., `process_event_task`, `synthesis_task`) and maps them to specific queues (e.g., `high_priority`, `low_priority`).

- **`core/`**: Contains the core application logic and configuration.

  - `config.py`: Manages application settings using Pydantic's `BaseSettings`, allowing for configuration via environment variables.
  - `redis.py`: Handles the creation and lifecycle of the Redis connection pool for the ARQ task queue.
  - `ws_connection_manager.py`: A utility to manage active WebSocket connections.

- **`models/`**: Defines the Pydantic models for the event data structures, ensuring that all incoming data is well-formed and validated.

- **`services/`**: Contains the service classes that provide an abstraction layer for interacting with external data stores and APIs.

  - `chroma_service.py`: Manages all interactions with the local ChromaDB instance, including adding documents and querying for similar insights.
  - `upstash_service.py`: Manages all interactions with the Upstash Vector DB, handling the public MCP Knowledge Base.
  - `llmservice.py`: Provides a unified interface for interacting with different LLMs (Ollama, Gemini).
  - `prompt_manager.py`: Manages the loading and rendering of Jinja2 prompt templates.

- **`pipelines/`**: Contains the modular Pipeline & Processor architecture.
  - `comprehension.py`: Defines the pipeline for processing raw events into insights.
  - `synthesis.py`: Defines the pipeline for synthesizing knowledge from multiple sources.
  - `curation.py`: Defines the multi-agent pipeline for augmenting public knowledge.
  - `delivery.py`: Defines the final pipeline step for delivering the insight to the user.

## 7. Current Operational Flow (Pipeline-based)

This diagram shows the current architecture. The core logic is handled by a modular Pipeline & Processor model. The `Comprehension Pipeline` processes raw events, and the `Synthesis Pipeline` combines insights from the private and public knowledge stores, and includes a gateway to trigger a curation pipeline if the public knowledge is insufficient.

```mermaid
graph TD
    subgraph "Git Observer"
        A[git commit]
    end

    subgraph "Cortex Backend"
        B(FastAPI Gateway)
        C(ARQ Task Queue)
        P[Comprehension Pipeline]
        S(Synthesis Pipeline)
        subgraph "Private Knowledge Pipeline"
            PKP[RunPrivatePipeline]
        end
        subgraph "Public Knowledge Pipeline"
            PUBP[RunPublicPipeline]
        end
    end

    subgraph "Data Stores"
        F[ChromaDB]
        G[Upstash]
        H[Markdown KG]
    end

    A -- Raw Event --> B
    B -- Enqueues L1 Job --> C
    C -- Dispatches --> P
    P -- Writes to --> F
    P -- Writes to --> H
    P -- Triggers L2 Job --> C
    C -- Dispatches --> S
    S -- runs in parallel --> PKP
    S -- runs in parallel --> PUBP
    PKP -- Queries --> F
    PKP -- Traverses --> H
    PUBP -- Queries --> G
    PUBP -- Augments --> G
```

## 6. Refactoring to a Pipeline & Processor Model

To create a more modular, scalable, and testable system, the current agent-based logic has been refactored into a formal **Pipeline & Processor** architecture. In this model, a "Pipeline" is responsible for executing a series of self-contained, reusable "Processors," with each processor handling one specific unit of work.

This diagram provides the blueprint for the implemented Level 1 Comprehension Pipeline, showing a `Pipeline` object that composes and executes a series of `Processor` objects.

```mermaid
graph TD
    subgraph "ARQ Worker"
        A["Start: Raw Event Data"]
        B(Build & Execute Pipeline)
    end

    subgraph "Pipeline Execution"
        direction LR
        C(Pipeline) -- contains --> P1[P1: EventDeserializer]
        C -- contains --> P2[P2: InsightGenerator]
        subgraph "Parallel Final Steps"
            P3[P3: KnowledgeGraphWriter]
            P4[P4: ChromaWriter]
            P5[P5: SynthesisTrigger]
        end
        C -- contains --> P3
        C -- contains --> P4
        C -- contains --> P5
    end

    %% Data Transformation Flow
    subgraph "Data Lifecycle"
        direction LR
        D1[Dict] --> D2[Event Model] --> D3[Insight Model]
    end

    %% Link Execution to Data
    A --> B
    B -- Executes --> C

    subgraph "Processor Sequence"
        direction LR
        B -- "initial_data(D1)" --> P1
        P1 -- "output(D2)" --> P2
        P2 -- "output(D3)" --> P3
        P2 -- "output(D3)" --> P4
        P2 -- "output(D3)" --> P5
    end
```

This diagram shows the Synthesis Pipeline, which runs the private and public knowledge retrieval pipelines in parallel before synthesizing the final result and delivering it.

```mermaid
graph TD
    subgraph "ARQ Worker"
        A["Start: Query Text"]
        B(Build & Execute Synthesis Pipeline)
    end

    subgraph "Main Synthesis Pipeline"
        direction LR
        subgraph "Parallel Sub-Pipelines"
            P1[RunPrivatePipeline]
            P2[RunPublicPipeline]
        end
        C(Pipeline) -- contains --> P1
        C(Pipeline) -- contains --> P2
        C(Pipeline) -- contains --> P3[InsightSynthesizer]
        C -- contains --> P4[AudioDeliveryProcessor]
    end

    %% Data Transformation Flow
    subgraph "Data Lifecycle"
        direction LR
        D1[String] --> D2_Private[Dict]
        D1 --> D2_Public[Dict]
        D2_Private --> D3[Dict]
        D2_Public --> D3[Dict]
    end

    %% Link Execution to Data
    A --> B
    B -- Executes --> C

    subgraph "Processor Sequence"
        direction LR
        B -- "initial_data(D1)" --> P1
        B -- "initial_data(D1)" --> P2
        P1 -- "output(D2_Private)" --> P3
        P2 -- "output(D2_Public)" --> P3
        P3 -- "output(Dict)" --> P4
    end
```

This diagram shows the Private Knowledge Pipeline:

```mermaid
graph TD
    subgraph "Private Knowledge Pipeline"
        direction LR
        A["Start: Query Text"]
        B(Pipeline) -- contains --> P1[PrivateKnowledgeQuerier]
        B -- contains --> P2[GraphTraversalProcessor]
        P1 -- "output(Dict)" --> P2
        A -- "initial_data(String)" --> P1
    end
```

This diagram shows the Public Knowledge Pipeline:

```mermaid
graph TD
    subgraph "Public Knowledge Pipeline"
        direction LR
        A["Start: Query Text"]
        B(Pipeline) -- contains --> P1[PublicKnowledgeQuerier]
        B -- contains --> P2[KnowledgeGatewayProcessor]
        B -- contains --> P3[CurationTriggerProcessor]
        P1 -- "output(Dict)" --> P2
        P2 -- "output(Dict)" --> P3
        A -- "initial_data(String)" --> P1
    end
```

### Flow Description:

1.  **Execution**: An ARQ task receives the raw event data and constructs a `Pipeline` composed of specific processors.
2.  **Processing**: The pipeline executes the processors in sequence:
    - `EventDeserializer`: Parses the raw dictionary into a validated Pydantic `Event` model.
    - `InsightGenerator`: Takes the `Event` model, calls the `LLMService`, and produces a structured `Insight` object.
    - `KnowledgeGraphWriter`: Appends the human-readable insight to the Markdown knowledge graph.
    - `ChromaWriter`: Adds the machine-readable embedding to the ChromaDB index.
    - `SynthesisTrigger`: Enqueues a new job for the next pipeline (e.g., the Synthesis Pipeline).
3.  **Data Flow**: The output of each processor becomes the input for the next, allowing data to be progressively enriched and transformed as it moves through the pipeline.

## 8. Real-time Multi-Modal Insight Delivery

This diagram details the final stage of the process: delivering the synthesized insight to the user as a real-time audio stream. This flow decouples the background processing from the client-facing web server using a Redis Pub/Sub message bus.

```mermaid
graph TD
    subgraph "ARQ Worker (Background Process)"
        A["<b>Synthesis Pipeline</b><br/>(Final Stage)"]
        P4[AudioDeliveryProcessor]
        TTS[Gemini TTS API]

        A -- "1. Final Insight (Text)" --> P4
        P4 -- "2. Generates Audio" --> TTS
        TTS -- "3. Returns Audio Data" --> P4
    end

    subgraph "Redis (Message Bus)"
        R[("Pub/Sub Channel<br/>'insights_channel'")]
        P4 -- "4. Publishes Audio Data" --> R
    end

    subgraph "FastAPI Server (Web Process)"
        WSS["<b>WebSocket Manager</b><br/>(Listens to Redis)"]
        WSC(Active WebSocket<br/>Connections)

        R -- "5. Receives Message" --> WSS
        WSS -- "6. Broadcasts Audio Data" --> WSC
    end

    subgraph "User's Local Machine"
        UI[IDE Plugin / Client UI]

        WSC -- "7. Streams Audio" --> UI
        UI -- "8. Plays Audio" --> User([User])
    end

    style A fill:#D5F5E3,stroke:#2ECC71
    style P4 fill:#D5F5E3,stroke:#2ECC71
    style WSS fill:#D6EAF8,stroke:#3498DB
    style UI fill:#FADBD8,stroke:#C0392B
```

### Flow Description:

1.  **Final Insight**: The `Synthesis Pipeline` completes its work, producing a final, human-readable insight as a string of text.
2.  **Audio Generation**: This text is passed to the `AudioDeliveryProcessor`. This processor makes an API call to the **Google Gemini TTS service** to convert the text into high-quality MP3 audio data.
3.  **Payload Construction**: The processor constructs a structured JSON object containing both the original **text insight** and the **Base64-encoded audio**.
4.  **Publish to Redis**: The `AudioDeliveryProcessor` publishes this JSON payload to the `insights_channel` Redis Pub/Sub channel.
5.  **Receive Message**: The FastAPI `WebSocketManager` receives the message.
6.  **Broadcast to Clients**: The manager broadcasts the JSON payload to all connected clients.
7.  **Render in UI**: The VS Code extension's **Chat View** parses the JSON. It displays the text in a chat bubble and creates an HTML5 audio player for the MP3 data.
8.  **Playback & Persistence**: The UI plays the audio (auto-play) and persists the message in the chat history, allowing the user to read and replay the insight later.
