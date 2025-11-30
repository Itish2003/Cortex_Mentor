# Testing Guide

## Current Test Coverage

**Status**: ⚠️ Testing infrastructure is minimal

**Test Files**: 3 files
- `tests/test_main.py` (0 functions)
- `tests/test_workers.py` (0 functions)  
- `tests/test_utils.py` (0 functions)

**Test Functions**: 0
**Coverage**: ~0%

**Recommendation**: Prioritize building comprehensive test suite.

## Recommended Test Structure

```
tests/
├── unit/                           # Unit tests (isolated components)
│   ├── test_processors.py         # Individual processor tests
│   ├── test_services.py           # Service layer tests
│   ├── test_models.py             # Pydantic model validation tests
│   └── test_pipelines.py          # Pipeline orchestration tests
├── integration/                    # Integration tests (multiple components)
│   ├── test_comprehension_flow.py # End-to-end comprehension pipeline
│   ├── test_synthesis_flow.py     # End-to-end synthesis pipeline
│   └── test_api.py                # API endpoint tests
├── e2e/                           # End-to-end tests (full system)
│   ├── test_git_commit_flow.py    # Git commit → insight → audio
│   └── test_websocket.py          # WebSocket delivery
├── fixtures/                      # Shared test data
│   ├── events.py                  # Sample events
│   ├── insights.py                # Sample insights
│   └── responses.py               # Mock LLM responses
└── conftest.py                    # Pytest configuration and fixtures
```

## Testing Patterns

### 1. Unit Testing Processors

**Pattern**: Test processors in isolation with mocked dependencies.

```python
# tests/unit/test_processors.py
import pytest
from cortex.pipelines.comprehension import InsightGenerator
from cortex.models.events import GitCommitEvent
from cortex.models.insights import Insight

@pytest.mark.asyncio
async def test_insight_generator_git_commit(mock_llm_service):
    """Test InsightGenerator with GitCommitEvent."""
    # Arrange
    processor = InsightGenerator(llm_service=mock_llm_service)
    event = GitCommitEvent(
        event_type="git_commit",
        repo_name="test-repo",
        branch_name="main",
        commit_hash="abc123def",
        message="feat: Add new feature",
        author_name="Test User",
        author_email="test@example.com",
        timestamp="2025-01-15T10:30:00Z",
        diff="diff --git a/test.py b/test.py\n+print('hello')"
    )
    context = {}
    
    # Act
    result = await processor.process(event, context)
    
    # Assert
    assert isinstance(result, Insight)
    assert result.source_event_type == "git_commit"
    assert result.summary == "Mock commit summary"  # From mock service
    assert result.metadata["repo_name"] == "test-repo"
    assert result.metadata["commit_hash"] == "abc123def"
    assert "Mock commit summary" in result.content_for_embedding

@pytest.mark.asyncio
async def test_insight_generator_code_change(mock_llm_service):
    """Test InsightGenerator with CodeChangeEvent."""
    # Similar structure for CodeChangeEvent
    pass

@pytest.mark.asyncio
async def test_insight_generator_unsupported_event(mock_llm_service):
    """Test InsightGenerator raises error for unsupported event."""
    processor = InsightGenerator(llm_service=mock_llm_service)
    
    with pytest.raises(TypeError, match="Unsupported event type"):
        await processor.process({"unknown": "event"}, {})
```

### 2. Mocking Services

**Pattern**: Create mock services that mimic real service interfaces.

```python
# tests/fixtures/services.py
class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self):
        self.generate_commit_summary_called = False
        self.generate_code_change_summary_called = False
    
    def generate_commit_summary(self, commit_message: str, commit_diff: str) -> str:
        self.generate_commit_summary_called = True
        return "Mock commit summary"
    
    def generate_code_change_summary(self, file_path: str, change_type: str, content: str) -> str:
        self.generate_code_change_summary_called = True
        return "Mock code change summary"

# tests/conftest.py
import pytest

@pytest.fixture
def mock_llm_service():
    """Provide mock LLM service."""
    return MockLLMService()

@pytest.fixture
def mock_chroma_service():
    """Provide mock ChromaDB service."""
    return MockChromaService()
```

### 3. Testing Pipelines

**Pattern**: Test pipeline orchestration with real or mocked processors.

```python
# tests/unit/test_pipelines.py
import pytest
from cortex.pipelines.pipelines import Pipeline
from cortex.pipelines.processors import Processor

class DoubleProcessor(Processor):
    """Test processor that doubles input."""
    async def process(self, data: int, context: dict) -> int:
        return data * 2

class AddTenProcessor(Processor):
    """Test processor that adds 10."""
    async def process(self, data: int, context: dict) -> int:
        return data + 10

@pytest.mark.asyncio
async def test_pipeline_sequential():
    """Test sequential pipeline execution."""
    pipeline = Pipeline([
        DoubleProcessor(),  # 5 → 10
        AddTenProcessor(),  # 10 → 20
    ])
    
    result = await pipeline.run(initial_data=5, context={})
    assert result == 20

@pytest.mark.asyncio
async def test_pipeline_parallel():
    """Test parallel pipeline execution."""
    class FirstResultProcessor(Processor):
        async def process(self, data: int, context: dict) -> int:
            return data[0]  # Get first result from parallel stage
    
    pipeline = Pipeline([
        DoubleProcessor(),  # 5 → 10
        [  # Parallel stage
            AddTenProcessor(),  # 10 → 20
            DoubleProcessor(),  # 10 → 20
        ],
        FirstResultProcessor(),  # [20, 20] → 20
    ])
    
    result = await pipeline.run(initial_data=5, context={})
    assert result == 20
```

### 4. Testing API Endpoints

**Pattern**: Use FastAPI TestClient for API testing.

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from cortex.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_post_git_commit_event(mock_redis_pool):
    """Test git commit event ingestion."""
    event_data = {
        "event_type": "git_commit",
        "repo_name": "test-repo",
        "branch_name": "main",
        "commit_hash": "abc123",
        "message": "feat: Test commit",
        "author_name": "Test User",
        "author_email": "test@example.com",
        "timestamp": "2025-01-15T10:30:00Z",
        "diff": "diff --git a/test.py..."
    }
    
    response = client.post("/api/events", json=event_data)
    
    assert response.status_code == 200
    assert "event_id" in response.json()
    # Verify task was enqueued to Redis (check mock)
    assert mock_redis_pool.enqueue_job_called

def test_post_invalid_event():
    """Test invalid event returns 422."""
    invalid_event = {
        "event_type": "git_commit",
        # Missing required fields
    }
    
    response = client.post("/api/events", json=invalid_event)
    assert response.status_code == 422
```

### 5. Testing WebSocket

**Pattern**: Test WebSocket connections and message broadcasting.

```python
# tests/e2e/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from cortex.main import app

def test_websocket_connection():
    """Test WebSocket connection establishment."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        # Connection successful
        assert websocket is not None

@pytest.mark.asyncio
async def test_websocket_insight_delivery(mock_redis_pubsub):
    """Test insight delivery via WebSocket."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        # Simulate Redis Pub/Sub message
        test_message = {
            "type": "insight",
            "text": "Test insight",
            "audio": "base64_audio_data"
        }
        await mock_redis_pubsub.publish("insights_channel", test_message)
        
        # Receive message via WebSocket
        data = websocket.receive_json()
        assert data["type"] == "insight"
        assert data["text"] == "Test insight"
```

### 6. Testing ARQ Tasks

**Pattern**: Test ARQ task functions with mocked context.

```python
# tests/unit/test_workers.py
import pytest
from cortex.workers import comprehension_task, synthesis_task

@pytest.mark.asyncio
async def test_comprehension_task(mock_worker_context):
    """Test comprehension task execution."""
    event_data = {
        "event_type": "git_commit",
        "repo_name": "test-repo",
        # ... other fields
    }
    
    result = await comprehension_task(mock_worker_context, event_data)
    
    assert "Processed git_commit event" in result
    # Verify pipeline was executed
    assert mock_worker_context['comprehension_pipeline'].run_called

@pytest.mark.asyncio
async def test_synthesis_task(mock_worker_context):
    """Test synthesis task execution."""
    query = "Test query for synthesis"
    
    result = await synthesis_task(mock_worker_context, query)
    
    assert "Synthesis complete" in result
    # Verify both private and public knowledge were queried
    assert mock_worker_context['synthesis_pipeline'].run_called
```

### 7. Testing Pydantic Models

**Pattern**: Test model validation and serialization.

```python
# tests/unit/test_models.py
import pytest
from pydantic import ValidationError
from cortex.models.events import GitCommitEvent, CodeChangeEvent

def test_git_commit_event_valid():
    """Test valid GitCommitEvent creation."""
    event = GitCommitEvent(
        event_type="git_commit",
        repo_name="test-repo",
        branch_name="main",
        commit_hash="abc123def456",
        message="feat: Add feature",
        author_name="Test User",
        author_email="test@example.com",
        timestamp="2025-01-15T10:30:00Z"
    )
    
    assert event.event_type == "git_commit"
    assert event.repo_name == "test-repo"

def test_git_commit_event_invalid_hash():
    """Test GitCommitEvent rejects invalid commit hash."""
    with pytest.raises(ValidationError, match="commit_hash"):
        GitCommitEvent(
            event_type="git_commit",
            commit_hash="abc",  # Too short (< 7 chars)
            # ... other fields
        )

def test_event_serialization():
    """Test event JSON serialization."""
    event = GitCommitEvent(...)
    json_data = event.model_dump_json()
    
    # Deserialize and verify
    reconstructed = GitCommitEvent.model_validate_json(json_data)
    assert reconstructed.commit_hash == event.commit_hash
```

### 8. Integration Testing (End-to-End Flows)

**Pattern**: Test complete workflows from event ingestion to output.

```python
# tests/integration/test_comprehension_flow.py
import pytest
from cortex.pipelines.comprehension import (
    EventDeserializer,
    InsightGenerator,
    KnowledgeGraphWriter,
    ChromaWriter,
)
from cortex.pipelines.pipelines import Pipeline

@pytest.mark.asyncio
async def test_comprehension_pipeline_git_commit(
    mock_llm_service,
    mock_kg_service,
    mock_chroma_service,
    tmp_path
):
    """Test full comprehension pipeline with git commit."""
    # Build pipeline
    pipeline = Pipeline([
        EventDeserializer(),
        InsightGenerator(llm_service=mock_llm_service),
        [
            KnowledgeGraphWriter(kg_service=mock_kg_service),
            ChromaWriter(chroma_service=mock_chroma_service),
        ],
    ])
    
    # Input event
    event_data = {
        "event_type": "git_commit",
        "repo_name": "test-repo",
        # ... complete event data
    }
    
    context = {}
    
    # Execute pipeline
    result = await pipeline.run(event_data, context)
    
    # Verify insight was generated
    assert result is None  # Final processor returns None
    
    # Verify side effects
    assert mock_kg_service.process_insight_called
    assert mock_chroma_service.add_document_called
```

## Pytest Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from pathlib import Path

# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test data fixtures
@pytest.fixture
def sample_git_commit_event():
    """Provide sample GitCommitEvent data."""
    return {
        "event_type": "git_commit",
        "repo_name": "test-repo",
        "branch_name": "main",
        "commit_hash": "abc123def456",
        "message": "feat: Add new feature",
        "author_name": "Test User",
        "author_email": "test@example.com",
        "timestamp": "2025-01-15T10:30:00Z",
        "diff": "diff --git a/test.py b/test.py\n+print('hello')"
    }

@pytest.fixture
def temp_knowledge_graph(tmp_path):
    """Provide temporary knowledge graph directory."""
    kg_path = tmp_path / "knowledge_graph"
    kg_path.mkdir()
    (kg_path / "insights").mkdir()
    (kg_path / "vector_db").mkdir()
    return kg_path

# Service mocks
@pytest.fixture
def mock_llm_service():
    """Provide mock LLM service."""
    from tests.fixtures.services import MockLLMService
    return MockLLMService()

@pytest.fixture
def mock_redis_pool():
    """Provide mock Redis pool."""
    from tests.fixtures.services import MockRedisPool
    return MockRedisPool()
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_processors.py -v

# Run tests matching pattern
pytest tests/ -k "test_insight" -v

# Run with coverage
pytest tests/ --cov=src/cortex --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with markers
pytest tests/ -m "slow" -v  # Only slow tests
pytest tests/ -m "not slow" -v  # Skip slow tests
```

## Coverage Goals

**Recommended Coverage Targets**:

- **Unit Tests**: 80%+ coverage for processors, services, models
- **Integration Tests**: Cover all major pipelines and workflows
- **E2E Tests**: Cover critical user journeys (commit → insight → audio)

**Priority Areas**:
1. Processors (comprehension, synthesis, curation)
2. Service layer (LLMService, ChromaService, KnowledgeGraphService)
3. Pydantic models (validation logic)
4. API endpoints (event ingestion)
5. Pipeline orchestration (sequential/parallel execution)

## Continuous Integration

**Recommended CI Pipeline** (GitHub Actions):

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .[dev]
      
      - name: Run tests
        run: pytest tests/ --cov=src/cortex --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Testing Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Mock External Services**: Don't hit real APIs in tests
3. **Use Fixtures**: Share test data via pytest fixtures
4. **Test Edge Cases**: Invalid inputs, missing fields, errors
5. **Fast Tests**: Unit tests should run in milliseconds
6. **Async Tests**: Use `@pytest.mark.asyncio` for async functions
7. **Clear Assertions**: Use descriptive assertion messages
8. **Test Privacy**: Verify no user data leaks to cloud services
9. **Test Parallel Execution**: Ensure processors work concurrently
10. **Test Error Handling**: Verify errors are caught and logged correctly
