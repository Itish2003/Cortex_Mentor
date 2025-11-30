# Backend Patterns

## Pipeline & Processor Architecture

### Core Pattern

The entire backend is built on a **Pipeline & Processor** pattern that enables modular, testable, and composable data processing.

**Location**: `src/cortex/pipelines/`

### Pipeline Class

**File**: `src/cortex/pipelines/pipelines.py:9`

```python
class Pipeline:
    def __init__(self, processors: List[Union[Processor, List[Processor]]]):
        self.processors = processors
    
    async def execute(self, data: Any, context: dict) -> Any:
        # Executes processors sequentially
        # Lists of processors execute in parallel
        ...
```

**Key Features**:
- Sequential execution: Pass processors in a list
- Parallel execution: Pass a list of lists `[[processor1, processor2]]`
- Async-first design
- Exception handling with logging
- Context passing for shared resources

### Processor Abstract Base Class

**File**: `src/cortex/pipelines/processors.py:4`

```python
class Processor(ABC):
    @abstractmethod
    async def process(self, data: Any, context: dict) -> Any:
        """Process input data and return result"""
        pass
```

**Design Principles**:
1. **Dependency Injection**: Inject services via constructor, NOT context
2. **Stateless Processing**: Each call should be independent
3. **Async by Default**: All processors are async
4. **Type Safety**: Use Pydantic models for data validation
5. **Logging**: Log entry/exit and errors

### Example: Creating a New Processor

```python
# src/cortex/pipelines/my_processor.py
from cortex.pipelines.processors import Processor
from cortex.services.my_service import MyService
import logging

logger = logging.getLogger(__name__)

class MyProcessor(Processor):
    """
    Does something specific with data.
    """
    def __init__(self, my_service: MyService):
        # GOOD: Inject dependencies via constructor
        self.my_service = my_service
    
    async def process(self, data: dict, context: dict) -> dict:
        logger.info("Processing with MyProcessor...")
        
        try:
            result = await self.my_service.do_something(data)
            logger.info("MyProcessor completed successfully")
            return result
        except Exception as e:
            logger.error(f"MyProcessor failed: {e}")
            raise
```

**Usage in Pipeline**:
```python
# src/cortex/workers.py
from cortex.services.my_service import MyService
from cortex.pipelines.my_processor import MyProcessor

my_service = MyService()  # Instantiate service
pipeline = Pipeline([
    SomeProcessor(),
    MyProcessor(my_service),  # Inject here
    AnotherProcessor(),
])
```

## Service Layer Pattern

### Service Organization

**Location**: `src/cortex/services/`

Services encapsulate external integrations and business logic:
- `llmservice.py` - LLM abstraction (Ollama + Gemini)
- `chroma_service.py` - ChromaDB operations
- `knowledge_graph_service.py` - Markdown file management
- `upstash_service.py` - Upstash vector DB client
- `prompt_manager.py` - Jinja2 template rendering

### LLMService Pattern

**File**: `src/cortex/services/llmservice.py:10`

**Key Features**:
- **Hybrid Model Support**: Automatically routes to Ollama (local) or Gemini (cloud) based on model name
- **Configuration-Driven**: Uses Pydantic Settings for model selection
- **Prompt Templates**: Integrates with PromptManager for Jinja2 templates

```python
class LLMService:
    def __init__(self):
        self.settings = Settings()
        self.prompt_manager = PromptManager()
        self._gemini_client = genai.Client()
    
    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        model_to_use = model or self.settings.llm_model
        
        if model_to_use.startswith("gemini-"):
            return self._generate_with_gemini(prompt, model_to_use)
        else:
            return self._generate_with_ollama(prompt, model_to_use)
```

**Usage Pattern**:
```python
llm_service = LLMService()

# Local Ollama (private data)
summary = llm_service.generate(
    prompt=f"Summarize: {user_code}",
    model="llama3.1:latest"
)

# Cloud Gemini (public data)
insight = llm_service.generate(
    prompt=synthesis_prompt,
    model=llm_service.settings.gemini_pro_model
)
```

### ChromaService Pattern

**File**: `src/cortex/services/chroma_service.py`

**Key Operations**:
- `add_document(doc_id, content, metadata)` - Embeds and stores
- `query(query_text, n_results)` - Semantic search
- Uses local Ollama embeddings (`nomic-embed-text:v1.5`)

**Pattern**:
```python
chroma_service = ChromaService()

# Add with metadata
chroma_service.add_document(
    doc_id=insight.insight_id,
    content=insight.content_for_embedding,
    metadata={
        "file_path": "src/data/knowledge_graph/insights/commit_abc123.md",
        "commit_hash": "abc123",
        "repo_name": "cortex_mentor"
    }
)

# Query
results = chroma_service.query("authentication patterns", n_results=5)
# Returns: {"documents": [...], "metadatas": [...], "distances": [...]}
```

### KnowledgeGraphService Pattern

**File**: `src/cortex/services/knowledge_graph_service.py`

**Key Concept**: Zettelkasten-style interlinked markdown files

**Pattern**:
```python
kg_service = KnowledgeGraphService()

# Writes markdown file with front matter
kg_service.process_insight(insight)

# Creates file: data/knowledge_graph/insights/commit_abc123.md
```

**Markdown Format**:
```markdown
---
insight_id: commit_abc123
source_event_type: git_commit
timestamp: 2024-11-29T12:00:00Z
tags: [authentication, security]
---

# Summary
Added JWT authentication to API endpoints

## Related Insights
- [[commit_xyz789]] - OAuth implementation
- [[code_def456]] - Token validation logic

## Metadata
- Repo: cortex_mentor
- Branch: main
- Commit: abc123...
```

## API Design Patterns

### Event Ingestion Pattern

**File**: `src/cortex/api/events.py`

**Pattern**: FastAPI router with Pydantic validation + ARQ task enqueue

```python
from fastapi import APIRouter, Request
from cortex.models.events import GitCommitEvent, CodeChangeEvent

router = APIRouter()

@router.post("/events")
async def receive_event(event_data: dict, request: Request):
    """
    Receives events from observers and enqueues for processing.
    """
    event_type = event_data.get("event_type")
    
    # Enqueue to ARQ worker
    redis = request.app.state.redis
    await redis.enqueue_job('process_event_task', event_data)
    
    return {"status": "queued", "event_type": event_type}
```

**Design Decisions**:
- **Async by default**: All endpoints are async
- **Validation**: Use Pydantic models for request/response
- **Queue immediately**: Don't process in HTTP handler, enqueue to worker
- **Return quickly**: Acknowledge receipt, process asynchronously

### WebSocket Pattern

**File**: `src/cortex/main.py:35`

**Pattern**: Long-lived connection with broadcast capability

```python
from cortex.core.ws_connection_manager import ConnectionManager

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep alive indefinitely
        await asyncio.Future()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**ConnectionManager Pattern**:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast(self, message: bytes):
        for connection in self.active_connections:
            await connection.send_bytes(message)
```

## Background Task Patterns

### ARQ Task Pattern

**File**: `src/cortex/workers.py`

**Pattern**: Define async functions + WorkerSettings class

```python
async def process_event_task(ctx, event_data: dict):
    """ARQ task to process events"""
    # 1. Instantiate services (fresh for each task)
    kg_service = KnowledgeGraphService()
    chroma_service = ChromaService()
    llm_service = LLMService()
    
    # 2. Build pipeline with injected dependencies
    pipeline = Pipeline([...])
    
    # 3. Execute with context
    context = {"redis": ctx.get("redis")}
    await pipeline.execute(data=event_data, context=context)

class WorkerSettings:
    functions = [process_event_task, synthesis_task]
    queues = ['high_priority', 'low_priority']
    on_startup = on_startup      # Creates Redis pool
    on_shutdown = on_shutdown    # Closes Redis pool
```

**Key Patterns**:
1. **Per-task service instantiation**: Fresh instances for each task
2. **Context for shared resources**: Redis pool in context
3. **Dependency injection**: Services injected into processors
4. **Lifecycle hooks**: `on_startup`/`on_shutdown` for resource management

### Redis Pub/Sub Pattern

**File**: `src/cortex/main.py:47`

**Pattern**: Background task subscribes to channel, broadcasts to WebSocket clients

```python
async def redis_pubsub_listener(app: FastAPI):
    redis = app.state.redis
    pubsub = redis.pubsub()
    await pubsub.subscribe("insights_channel")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message["type"] == "message":
                data = message["data"]  # bytes
                await manager.broadcast(data)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        await pubsub.unsubscribe("insights_channel")
```

**Publishing Pattern**:
```python
# In AudioDeliveryProcessor
async def process(self, data: dict, context: dict) -> None:
    redis = context["redis"]
    audio_bytes = generate_audio(data["final_insight"])
    await redis.publish("insights_channel", audio_bytes)
```

## Multi-Agent Pattern

### Google ADK Agent Pattern

**File**: `src/cortex/pipelines/synthesis.py:118` (KnowledgeGatewayProcessor)

**Critical Pattern**: Instantiate agents per-request to avoid session state reuse

```python
from google.adk.agents import LlmAgent
from cortex.utility.agent_runner import run_standalone_agent

class MyProcessor(Processor):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        # DON'T instantiate agent here!
    
    async def process(self, data: dict, context: dict) -> dict:
        # GOOD: Instantiate fresh agent for each request
        agent = LlmAgent(
            name="my_agent",
            instruction=self.prompt_manager.render("agent_prompt.jinja2"),
            output_schema=MyOutputModel,
            model=self.llm_service.settings.gemini_flash_model,
        )
        
        result = await run_standalone_agent(agent, user_prompt)
        return result
```

**Why**: Google ADK agents maintain session state. Reusing instances across requests causes context bleeding.

### Structured Output Pattern

```python
from pydantic import BaseModel

class GatewayDecision(BaseModel):
    needs_improvement: bool
    reasoning: str

agent = LlmAgent(
    name="gateway_agent",
    instruction="Evaluate knowledge quality...",
    output_schema=GatewayDecision,  # Forces JSON output
)

result = await run_standalone_agent(agent, prompt)
decision = GatewayDecision.model_validate_json(result)
```

## Configuration Pattern

### Pydantic Settings Pattern

**File**: `src/cortex/core/config.py`

```python
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Computed paths (relative to source)
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/...")
    
    # Environment variables
    upstash_url: str = ""
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Defaults
    llm_model: str = "llama3.1:latest"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
```

**Usage**:
```python
settings = Settings()  # Reads .env automatically
print(settings.gemini_api_key)
```

## Error Handling Pattern

### Custom Exception Pattern

**File**: `src/cortex/exceptions.py`

```python
class ProcessorError(Exception):
    """Raised when a processor fails"""
    pass
```

**Usage in Processors**:
```python
try:
    result = await self.service.operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise ProcessorError(f"MyProcessor failed: {e}") from e
```

## Logging Pattern

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# In processor
logger.info(f"Processing {data.insight_id}...")
logger.error(f"Failed to process {data.insight_id}: {e}", exc_info=True)
logger.warning(f"Unexpected result: {result}")
```

**Configure in main**:
```python
logging.basicConfig(level=logging.INFO)
```

## Testing Patterns

### Test Structure

**Location**: `tests/`

**Pattern**: Pytest with async support

```python
import pytest
from cortex.pipelines.my_processor import MyProcessor

@pytest.mark.asyncio
async def test_my_processor():
    # Arrange
    processor = MyProcessor(mock_service)
    data = {"key": "value"}
    context = {}
    
    # Act
    result = await processor.process(data, context)
    
    # Assert
    assert result["key"] == "expected"
```

## Privacy Boundaries

### Local vs Cloud Processing

**Rule**: User code/commits/private data → Ollama (local only)

**Pattern**:
```python
# GOOD: Private data processed locally
llm_service.generate(
    prompt=f"Summarize commit: {commit_diff}",
    model="llama3.1:latest"  # Local Ollama
)

# GOOD: Public knowledge processed in cloud
llm_service.generate(
    prompt=f"Synthesize: {public_knowledge}",
    model=llm_service.settings.gemini_pro_model  # Cloud Gemini
)

# BAD: Sending user code to cloud
llm_service.generate(
    prompt=f"Analyze: {user_code}",
    model="gemini-2.5-pro"  # ❌ PRIVACY VIOLATION
)
```
