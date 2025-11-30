# System Architecture

## Architecture Pattern

**Pipeline-Based Event-Driven Architecture with Parallel Processing**

Cortex Mentor uses a sophisticated pipeline architecture where events flow through sequential and parallel processors. The system is built on a hybrid knowledge model that maintains strict privacy boundaries between local and cloud processing.

## Project Structure

```
cortex_mentor/
├── src/cortex/           # Main backend application
│   ├── main.py          # FastAPI app & WebSocket server
│   ├── workers.py       # ARQ background task definitions
│   ├── api/             # API endpoints
│   │   └── events.py    # Event ingestion endpoint
│   ├── pipelines/       # Modular pipeline architecture
│   │   ├── pipelines.py        # Core Pipeline class
│   │   ├── processors.py       # Abstract Processor base
│   │   ├── comprehension.py    # Event → Insight pipeline
│   │   ├── synthesis.py        # Knowledge synthesis pipeline
│   │   ├── curation.py         # Knowledge augmentation pipeline
│   │   ├── delivery.py         # Audio delivery processor
│   │   └── graph_traversal.py  # Knowledge graph traversal
│   ├── services/        # External service integrations
│   │   ├── llmservice.py              # Ollama + Gemini integration
│   │   ├── chroma_service.py          # ChromaDB vector ops
│   │   ├── knowledge_graph_service.py # Markdown knowledge graph
│   │   ├── upstash_service.py         # Public knowledge queries
│   │   └── prompt_manager.py          # Jinja2 prompt templates
│   ├── models/          # Pydantic data models
│   │   ├── events.py    # Event types (GitCommitEvent, CodeChangeEvent)
│   │   └── insights.py  # Insight model
│   ├── core/            # Core infrastructure
│   │   ├── config.py              # Pydantic Settings
│   │   ├── redis.py               # Redis connection pool
│   │   └── ws_connection_manager.py  # WebSocket manager
│   ├── tools/           # Development tools
│   │   └── git_analyzer.py
│   └── utility/         # Utility functions
│       ├── utils.py
│       └── agent_runner.py  # Google ADK agent wrapper
├── data/knowledge_graph/  # Private knowledge storage
│   ├── insights/         # Markdown files (Zettelkasten)
│   └── vector_db/        # ChromaDB persistence
├── cortex-vs/           # VS Code extension (TypeScript)
├── observers/           # Workflow observers
├── tests/              # Test suite
└── docs/               # Documentation

```

## Layer Responsibilities

### 1. Observation Layer
- **Git Post-Commit Hook** (`observers/git/post-commit`): Captures commit metadata and diffs
- **File Watcher** (`src/cortex/tools/git_analyzer.py`): Monitors file system changes
- **VS Code Extension** (`cortex-vs/`): Tracks code edits, provides UI

### 2. API Gateway Layer
- **FastAPI Server** (`src/cortex/main.py`): HTTP API and WebSocket server
- **Event Ingestion Endpoint** (`src/cortex/api/events.py`): Validates and enqueues events
- **WebSocket Manager** (`src/cortex/core/ws_connection_manager.py`): Maintains client connections

### 3. Task Queue Layer
- **ARQ Worker** (`src/cortex/workers.py`): Async task processing with Redis
- **Redis** (`src/cortex/core/redis.py`): Message queue and Pub/Sub

### 4. Pipeline Processing Layer
- **Pipeline Orchestrator** (`src/cortex/pipelines/pipelines.py`): Manages sequential/parallel execution
- **Processors**: Modular, composable processing units
- **Parallel Execution**: Uses `asyncio.gather()` for concurrent processing

### 5. Service Integration Layer
- **LLM Service** (`src/cortex/services/llmservice.py`): Manages Ollama (local) and Gemini (cloud)
- **Vector DB Services**: ChromaDB (local), Upstash (cloud)
- **Knowledge Graph Service**: Markdown file management
- **Multi-Agent System**: Google ADK orchestration

## Complete Data Flow

```
Developer Action (commit/edit)
    ↓
Observer (Git hook / File watcher / VS Code extension)
    ↓
POST /api/events → FastAPI endpoint
    ↓
Event validation (Pydantic models)
    ↓
Enqueue to ARQ task queue → Redis
    ↓
ARQ Worker picks up task
    ↓
┌─────────────────────────────────────┐
│  COMPREHENSION PIPELINE             │
│  1. EventDeserializer               │
│  2. InsightGenerator (Ollama)       │
│  3. [Parallel]                      │
│     - KnowledgeGraphWriter          │
│     - ChromaWriter                  │
│  4. SynthesisTrigger                │
└─────────────────────────────────────┘
    ↓
Enqueue synthesis task → Redis
    ↓
ARQ Worker picks up synthesis task
    ↓
┌─────────────────────────────────────┐
│  SYNTHESIS PIPELINE (Parallel)      │
│  ┌─────────────────────────────┐   │
│  │ PRIVATE KNOWLEDGE PATH      │   │
│  │ - PrivateKnowledgeQuerier   │   │
│  │ - GraphTraversalProcessor   │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ PUBLIC KNOWLEDGE PATH       │   │
│  │ - PublicKnowledgeQuerier    │   │
│  │ - KnowledgeGatewayProcessor │   │
│  │ - CurationTriggerProcessor  │   │
│  └─────────────────────────────┘   │
│  → InsightSynthesizer (Gemini)     │
│  → AudioDeliveryProcessor (TTS)    │
└─────────────────────────────────────┘
    ↓
Publish to Redis insights_channel
    ↓
FastAPI redis_pubsub_listener receives
    ↓
WebSocket broadcast to all clients
    ↓
VS Code extension plays audio
```

## Pipeline & Processor Pattern

### Core Design

```python
class Processor(ABC):
    @abstractmethod
    async def process(self, data: Any, context: dict) -> Any:
        """
        Process data and return transformed result.
        Context contains shared resources like Redis, services.
        """
        pass

class Pipeline:
    def __init__(self, processors: List[Union[Processor, List[Processor]]]):
        self.processors = processors
    
    async def run(self, initial_data: Any, context: dict) -> Any:
        """
        Execute processors sequentially.
        If a processor is a list, execute all in parallel.
        """
        pass
```

### Example: Comprehension Pipeline

```python
comprehension_pipeline = Pipeline([
    EventDeserializer(),
    InsightGenerator(llm_service=llm_service),
    [  # Parallel execution
        KnowledgeGraphWriter(kg_service),
        ChromaWriter(chroma_service),
    ],
    SynthesisTrigger(),
])
```

## Hybrid Knowledge Model

### Private Knowledge (Local-First)

**Markdown Knowledge Graph** (`data/knowledge_graph/insights/`)
- Human-readable Zettelkasten-style files
- Source of truth for all insights
- Interlinked via `[[wikilinks]]`
- Organized by project/topic

**ChromaDB** (`data/knowledge_graph/vector_db/`)
- Local vector database for semantic search
- Embeddings generated by Ollama (nomic-embed-text:v1.5)
- Metadata points to markdown source files
- Performance layer for fast retrieval

**Privacy Guarantee**: All user code, commits, and private data processed locally with Ollama

### Public Knowledge (Cloud-Based)

**Upstash Vector Database**
- Curated software development knowledge
- Pre-populated with expert content
- Used for synthesis and augmentation
- No user-specific data stored

**Gemini Models** (Google AI)
- Complex reasoning and synthesis
- Web search analysis (via curation agents)
- Multi-agent orchestration
- Only receives anonymized queries

## Multi-Agent System

Uses Google ADK framework for complex reasoning tasks:

```python
from google.adk.agents import Agent
from cortex.utility.agent_runner import run_standalone_agent

# Per-request agent instantiation (critical for session state isolation)
agent = Agent(
    model="gemini-2.5-pro",
    instructions=prompt_manager.render("agent_instructions.j2"),
    tools=[web_search_tool],
)

result = await run_standalone_agent(
    agent=agent,
    user_message="Analyze this topic",
    response_schema=OutputSchema,  # Pydantic model
)
```

### Agent Patterns

1. **Sequential Agents** (Curation Pipeline):
   - Research Agent → Web Search Agent → Summarizer Agent
   - Each agent passes structured output to next

2. **Parallel Agents** (Synthesis Pipeline):
   - Private Knowledge Agent + Public Knowledge Agent run concurrently
   - Results merged by synthesizer

3. **Per-Request Instantiation**:
   - Agents created for each task to avoid session state bugs
   - No global agent instances

## WebSocket Real-Time Delivery

### Architecture

```
ARQ Worker (synthesis complete)
    ↓
Publish JSON to Redis insights_channel
    ↓
FastAPI Background Task: redis_pubsub_listener()
    ↓
ConnectionManager.broadcast(message)
    ↓
All WebSocket clients receive message
    ↓
VS Code extension decodes base64 audio
    ↓
Audio playback in IDE
```

### Message Format

```json
{
  "type": "insight",
  "text": "Summary of your recent commit...",
  "audio": "base64_encoded_mp3_data"
}
```

## Privacy Boundaries

### Local Processing (Ollama)
- Git commit analysis
- Code change summarization
- Private knowledge embeddings
- Local vector search

### Cloud Processing (Gemini)
- Insight synthesis (with anonymized context)
- Web search analysis
- Public knowledge queries
- Complex reasoning tasks

**Critical Rule**: User-specific code and commits NEVER sent to cloud services

## Design Patterns

1. **Dependency Injection**: Services injected into processors via constructor
2. **Async-First**: All I/O operations use `async/await`
3. **Pydantic Validation**: Strict typing for events, insights, and configurations
4. **Template-Based Prompts**: Jinja2 templates for LLM prompts
5. **Connection Pooling**: Redis connection pool for performance
6. **Graceful Degradation**: System continues if optional services fail
7. **Parallel Processing**: `asyncio.gather()` for concurrent operations

## Error Handling

- Custom exception hierarchy (`src/cortex/exceptions.py`):
  - `CortexError` (base)
  - `PipelineError`
  - `ProcessorError`
  - `ServiceError`
  - `WebsocketError`
  - `ConfigurationError`

- Processors log errors but don't crash pipeline
- Failed tasks re-enqueued by ARQ with exponential backoff
- WebSocket disconnections handled gracefully

## Configuration

All settings managed via `src/cortex/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    
    # Google AI
    gemini_api_key: str
    
    # Upstash
    upstash_url: str
    upstash_token: str
    
    # Paths
    knowledge_graph_path: Path = Path(__file__).parent.parent.parent / "data/knowledge_graph"
    
    class Config:
        env_file = ".env"
```

## Scalability Considerations

- **Horizontal Scaling**: Multiple ARQ workers can process tasks in parallel
- **Redis Pub/Sub**: Supports multiple WebSocket server instances
- **Stateless Processors**: Enable easy distributed processing
- **ChromaDB**: Can be replaced with hosted vector DB (Pinecone, Weaviate)
- **Agent Orchestration**: Per-request agents prevent session state conflicts
