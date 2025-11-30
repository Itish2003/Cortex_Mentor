# Backend Patterns & Best Practices

This document outlines the key patterns, conventions, and best practices used throughout the Cortex Mentor backend.

## Core Architectural Patterns

### 1. Pipeline & Processor Pattern

**Purpose**: Modular, composable async processing with sequential and parallel execution.

**Pattern Structure**:

```python
from abc import ABC, abstractmethod
from typing import Any, List, Union

class Processor(ABC):
    """
    Abstract base for all processors.
    Each processor is a self-contained unit with a single responsibility.
    """
    @abstractmethod
    async def process(self, data: Any, context: dict) -> Any:
        """
        Process input data and return transformed output.
        
        Args:
            data: Input data (type depends on processor position in pipeline)
            context: Shared resources (Redis, services, config)
        
        Returns:
            Transformed data for next processor
        """
        pass

class Pipeline:
    """
    Orchestrates sequential and parallel processor execution.
    """
    def __init__(self, processors: List[Union[Processor, List[Processor]]]):
        """
        Args:
            processors: List of processors or lists of processors.
                        If element is a list, those processors run in parallel.
        """
        self.processors = processors
    
    async def run(self, initial_data: Any, context: dict) -> Any:
        """
        Execute pipeline with sequential/parallel processing.
        """
        data = initial_data
        for stage in self.processors:
            if isinstance(stage, list):
                # Parallel execution
                results = await asyncio.gather(
                    *[p.process(data, context) for p in stage]
                )
                data = results[0] if results else data
            else:
                # Sequential execution
                data = await stage.process(data, context)
        return data
```

**Usage Example**:

```python
# Sequential pipeline
simple_pipeline = Pipeline([
    EventDeserializer(),
    InsightGenerator(llm_service),
    ChromaWriter(chroma_service),
])

# Pipeline with parallel stage
comprehension_pipeline = Pipeline([
    EventDeserializer(),
    InsightGenerator(llm_service),
    [  # These run concurrently
        KnowledgeGraphWriter(kg_service),
        ChromaWriter(chroma_service),
    ],
    SynthesisTrigger(),
])

# Execute
result = await pipeline.run(event_data, context)
```

**Why This Pattern**:
- ✅ Single Responsibility: Each processor has one job
- ✅ Composability: Mix and match processors easily
- ✅ Testability: Test processors in isolation
- ✅ Parallel Execution: Optimize I/O-bound operations
- ✅ Reusability: Processors can be used in multiple pipelines

### 2. Dependency Injection

**Pattern**: Inject services via constructor, not via context.

**❌ Anti-pattern**:

```python
class InsightGenerator(Processor):
    async def process(self, data, context):
        # BAD: Retrieving service from context
        llm_service = context['llm_service']
        result = llm_service.generate(data)
        return result
```

**✅ Recommended**:

```python
class InsightGenerator(Processor):
    def __init__(self, llm_service: LLMService):
        # GOOD: Inject service via constructor
        self.llm_service = llm_service
    
    async def process(self, data, context):
        # Service is already available
        result = self.llm_service.generate(data)
        return result
```

**Why This Pattern**:
- ✅ Type safety: Constructor parameters are typed
- ✅ Explicit dependencies: Clear what each processor needs
- ✅ Easier testing: Mock services in constructor
- ✅ Better IDE support: Autocomplete works correctly

**Context Usage**: Reserve `context` for runtime-only resources like Redis pool, not services.

### 3. Service Layer Pattern

**Pattern**: Encapsulate external integrations in service classes.

**Service Structure**:

```python
from cortex.core.config import Settings

class MyService:
    """
    Service for integrating with external system.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Private method to set up client."""
        return SomeClient(api_key=self.settings.api_key)
    
    async def query(self, input_text: str) -> dict:
        """Public async method for queries."""
        response = await self.client.query(input_text)
        return self._parse_response(response)
    
    def _parse_response(self, response) -> dict:
        """Private method to parse responses."""
        return {"result": response.data}
```

**Why This Pattern**:
- ✅ Separation of concerns: Business logic separated from integration details
- ✅ Reusability: Services used across multiple processors
- ✅ Testability: Mock services easily
- ✅ Centralized configuration: Settings managed in one place

**Examples in Codebase**:
- `LLMService`: Ollama + Gemini integration
- `ChromaService`: Vector database operations
- `KnowledgeGraphService`: Markdown file management
- `UpstashService`: Public knowledge queries

### 4. Pydantic Models for Data Validation

**Pattern**: Use Pydantic models for all data structures.

**Event Models** (`src/cortex/models/events.py`):

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SourceEvent(BaseModel):
    """Base class for all events."""
    event_type: str
    timestamp: datetime

class GitCommitEvent(SourceEvent):
    """Git commit event with strict validation."""
    event_type: str = "git_commit"
    repo_name: str
    branch_name: str
    commit_hash: str = Field(..., min_length=7, max_length=40)
    message: str
    author_name: str
    author_email: str
    diff: str | None = None
```

**Insight Models** (`src/cortex/models/insights.py`):

```python
class Insight(BaseModel):
    """Structured insight from event processing."""
    insight_id: str
    source_event_type: str
    summary: str
    patterns: List[str] = []
    metadata: dict = {}
    content_for_embedding: str
    source_event: SourceEvent | None = None
```

**Why This Pattern**:
- ✅ Automatic validation: Invalid data raises errors early
- ✅ Type safety: IDE autocomplete and type checking
- ✅ Documentation: Models serve as API documentation
- ✅ Serialization: Easy JSON conversion

### 5. Multi-Agent System Pattern

**Critical Pattern**: Per-request agent instantiation to avoid session state bugs.

**❌ Anti-pattern (Session State Bug)**:

```python
# WRONG: Global agent reused across requests
from google.adk.agents import Agent

# This agent accumulates state across multiple calls
GLOBAL_AGENT = Agent(
    model="gemini-2.5-pro",
    instructions="You are a research assistant.",
)

async def research_task(ctx, topic: str):
    # BUG: Agent remembers previous topics from other users!
    result = GLOBAL_AGENT.run(topic)
    return result
```

**✅ Recommended (Per-Request Instantiation)**:

```python
# CORRECT: Create new agent for each request
from cortex.utility.agent_runner import run_standalone_agent
from google.adk.agents import Agent

async def research_task(ctx, topic: str):
    # Create fresh agent with no session state
    agent = Agent(
        model="gemini-2.5-pro",
        instructions="You are a research assistant.",
        tools=[web_search_tool],
    )
    
    # Run agent and get structured output
    result = await run_standalone_agent(
        agent=agent,
        user_message=topic,
        response_schema=ResearchOutput,  # Pydantic model
    )
    return result
```

**Why This Pattern**:
- ✅ No session state leakage between requests
- ✅ Parallel agent execution is safe
- ✅ Predictable behavior: Each request is isolated
- ✅ Easier debugging: No hidden state

**Agent Orchestration Examples**:

```python
# Sequential agents (curation pipeline)
research_agent = Agent(model="gemini-2.5-pro", instructions="Research")
summarizer_agent = Agent(model="gemini-2.5-flash", instructions="Summarize")

research_result = await run_standalone_agent(research_agent, topic)
summary = await run_standalone_agent(summarizer_agent, research_result)

# Parallel agents (synthesis pipeline)
private_agent = Agent(model="gemini-2.5-flash", instructions="Query private KB")
public_agent = Agent(model="gemini-2.5-flash", instructions="Query public KB")

private_result, public_result = await asyncio.gather(
    run_standalone_agent(private_agent, query),
    run_standalone_agent(public_agent, query),
)
```

## ARQ Task Queue Patterns

### Task Definition

```python
# src/cortex/workers.py
async def comprehension_task(ctx: dict, event_data: dict) -> str:
    """
    ARQ task function.
    
    Args:
        ctx: Context with injected services from WorkerSettings
        event_data: Event payload
    
    Returns:
        Task result (logged by ARQ)
    """
    pipeline = ctx['comprehension_pipeline']
    context = {
        'redis': ctx['redis'],
        'settings': ctx['settings'],
    }
    
    try:
        await pipeline.run(event_data, context)
        return f"Processed {event_data.get('event_type')} event"
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise  # ARQ will retry with backoff
```

### Worker Settings

```python
class WorkerSettings:
    """ARQ worker configuration."""
    
    # Task functions to register
    functions = [comprehension_task, synthesis_task]
    
    # Redis connection
    redis_settings = RedisSettings(
        host='localhost',
        port=6379,
    )
    
    # Retry configuration
    max_tries = 3
    retry_backoff = True  # Exponential backoff
    
    # Startup: Inject services into context
    async def on_startup(ctx):
        ctx['llm_service'] = LLMService(settings)
        ctx['chroma_service'] = ChromaService(settings)
        ctx['comprehension_pipeline'] = build_comprehension_pipeline(ctx)
    
    # Shutdown: Cleanup resources
    async def on_shutdown(ctx):
        await ctx['redis'].close()
```

### Enqueuing Tasks

```python
from arq import create_pool
from cortex.core.redis import get_redis_pool

async def enqueue_event(event_data: dict):
    """Enqueue event for processing."""
    redis = await get_redis_pool()
    await redis.enqueue_job('comprehension_task', event_data)
```

## Error Handling Patterns

### Custom Exception Hierarchy

```python
# src/cortex/exceptions.py
class CortexError(Exception):
    """Base exception for all Cortex errors."""
    pass

class PipelineError(CortexError):
    """Error during pipeline execution."""
    pass

class ProcessorError(PipelineError):
    """Error in specific processor."""
    pass

class ServiceError(CortexError):
    """Error in service layer."""
    pass
```

### Processor Error Handling

```python
class RobustProcessor(Processor):
    async def process(self, data, context):
        try:
            result = await self.risky_operation(data)
            return result
        except SpecificError as e:
            logger.error(f"Failed to process {data}: {e}", exc_info=True)
            raise ProcessorError(f"Processing failed: {e}") from e
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            raise
```

### Graceful Degradation

```python
class OptionalProcessor(Processor):
    async def process(self, data, context):
        try:
            enrichment = await self.optional_enrichment(data)
            return {**data, "enrichment": enrichment}
        except Exception as e:
            logger.warning(f"Enrichment failed, continuing: {e}")
            # Return original data if enrichment fails
            return data
```

## Logging Patterns

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyProcessor(Processor):
    async def process(self, data, context):
        logger.info(
            "Processing event",
            extra={
                "event_type": data.get("event_type"),
                "processor": self.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        # ... processing logic
        logger.info("Event processed successfully")
```

### Log Levels

- `DEBUG`: Detailed diagnostic information (e.g., LLM prompts)
- `INFO`: General informational messages (e.g., task started/completed)
- `WARNING`: Something unexpected but handled (e.g., missing optional field)
- `ERROR`: Operation failed but recoverable (e.g., processor error)
- `CRITICAL`: System-level failure (e.g., Redis connection lost)

## Configuration Patterns

### Pydantic Settings

```python
# src/cortex/core/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Centralized configuration."""
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text:v1.5"
    
    # Google AI
    gemini_api_key: str  # Required, no default
    
    # Paths (resolve relative to project root)
    knowledge_graph_path: Path = Path(__file__).parent.parent.parent / "data/knowledge_graph"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Usage
settings = Settings()  # Auto-loads from .env
```

## Testing Patterns

### Processor Unit Tests

```python
import pytest
from cortex.pipelines.comprehension import InsightGenerator
from cortex.services.llmservice import LLMService

@pytest.mark.asyncio
async def test_insight_generator():
    # Arrange
    mock_llm = MockLLMService()
    processor = InsightGenerator(llm_service=mock_llm)
    event = GitCommitEvent(
        event_type="git_commit",
        repo_name="test-repo",
        # ... other fields
    )
    context = {}
    
    # Act
    result = await processor.process(event, context)
    
    # Assert
    assert isinstance(result, Insight)
    assert result.source_event_type == "git_commit"
    assert mock_llm.generate_called
```

### Service Mocking

```python
class MockLLMService:
    def __init__(self):
        self.generate_called = False
    
    def generate_commit_summary(self, commit_message, commit_diff):
        self.generate_called = True
        return "Mock summary"
```

## Privacy Patterns

### Local-First Processing

```python
class PrivateDataProcessor(Processor):
    def __init__(self, local_llm: LLMService):
        # Only use local Ollama for private data
        self.llm = local_llm
    
    async def process(self, user_code: str, context):
        # This NEVER goes to cloud
        summary = self.llm.generate_with_ollama(
            model="llama3.1:latest",
            prompt=f"Summarize: {user_code}"
        )
        return summary
```

### Cloud Processing (Anonymized)

```python
class PublicKnowledgeProcessor(Processor):
    def __init__(self, cloud_llm: LLMService):
        # OK to use cloud Gemini for public knowledge
        self.llm = cloud_llm
    
    async def process(self, anonymized_query: str, context):
        # No user-specific data in this query
        result = self.llm.generate_with_gemini(
            model="gemini-2.5-flash",
            prompt=f"Query knowledge base: {anonymized_query}"
        )
        return result
```

## Best Practices Summary

1. **Use Processors for Modularity**: Every processing step should be a processor
2. **Inject Dependencies**: Pass services via constructor, not context
3. **Per-Request Agents**: Never reuse Google ADK agents across requests
4. **Validate with Pydantic**: Use models for all data structures
5. **Parallel When Possible**: Use lists in pipelines for parallel execution
6. **Privacy-First**: Local Ollama for user data, cloud Gemini for synthesis
7. **Structured Logging**: Include context in log messages
8. **Graceful Degradation**: Handle optional failures without crashing
9. **Type Everything**: Use type hints for better IDE support and safety
10. **Test in Isolation**: Unit test processors with mocked services
