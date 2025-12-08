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

## Testing

Cortex Mentor has a comprehensive test suite covering both the Python backend and the TypeScript VS Code extension.

### Backend Testing (Python)

The backend uses `pytest` for testing with `pytest-asyncio` for async test support and `pytest-cov` for coverage reporting.

#### Running All Tests
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing
```

#### Running Specific Test Categories
```bash
# Run only unit tests (skip integration tests)
uv run pytest -m "not integration"

# Run only integration tests (mocked services)
uv run pytest tests/test_integration.py -v

# Run true E2E tests with real Redis (requires Redis running)
uv run pytest tests/test_e2e_real.py -v -m integration

# Run tests for a specific module
uv run pytest tests/test_pipelines.py -v
uv run pytest tests/test_comprehension.py -v
uv run pytest tests/test_workers.py -v
```

#### Running True E2E Tests

The `test_e2e_real.py` file contains tests that interact with real external services:

```bash
# Start Redis first
brew services start redis

# Run E2E tests with real services
uv run pytest tests/test_e2e_real.py -v -m integration

# Run specific E2E test class
uv run pytest tests/test_e2e_real.py::TestRealRedisConnection -v
uv run pytest tests/test_e2e_real.py::TestRealPipelineIntegration -v
```

These tests verify:
- Real Redis connectivity and pub/sub messaging
- API server endpoint responses
- WebSocket connection establishment
- Full pipeline execution with real Redis job enqueuing

#### Test Files Overview
| File | Description |
|------|-------------|
| `tests/test_services.py` | Tests for LLMService, ChromaService, UpstashService, KnowledgeGraphService |
| `tests/test_comprehension.py` | Tests for comprehension pipeline processors |
| `tests/test_curation.py` | Tests for curation pipeline and agent system |
| `tests/test_delivery.py` | Tests for audio delivery processor |
| `tests/test_graph_traversal.py` | Tests for knowledge graph traversal |
| `tests/test_pipelines.py` | Tests for synthesis pipeline processors |
| `tests/test_workers.py` | Tests for ARQ worker tasks |
| `tests/test_integration.py` | End-to-end integration tests (full front-to-back flow) |
| `tests/test_e2e_real.py` | True E2E tests with real Redis (requires running services) |
| `tests/test_api.py` | API endpoint tests |
| `tests/test_error_handling.py` | Error handling and edge case tests |

#### Coverage Requirements
- Minimum coverage threshold: **70%**
- Coverage reports are generated in `htmlcov/` directory
- CI/CD will fail if coverage drops below threshold

### VS Code Extension Testing (TypeScript)

The extension uses Mocha for testing with `c8` for coverage.

#### Running Extension Tests
```bash
cd cortex-vs

# Run all tests with coverage
npm test

# Run type checking
npm run check-types

# Run linting
npm run lint
```

#### Test Files Overview
| File | Description |
|------|-------------|
| `src/test/extension.test.ts` | Extension activation, command registration, configuration tests |
| `src/test/chatViewProvider.test.ts` | ChatViewProvider unit tests |
| `src/test/websocket.test.ts` | WebSocket client configuration, message parsing, connection state tests |

#### Coverage Requirements
- Minimum coverage threshold: **60%**

### CI/CD Workflows

GitHub Actions automatically runs tests on pull requests and pushes:

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `backend-tests.yml` | PR/Push to `src/`, `tests/` | Runs Python tests with coverage |
| `extension-tests.yml` | PR/Push to `cortex-vs/` | Runs TypeScript tests, linting, and build |
| `integration-tests.yml` | PR | Full integration tests with Redis |

#### Viewing Test Results
- Coverage reports are uploaded as artifacts on each CI run
- Coverage summaries appear in GitHub Actions job summaries
- Codecov integration provides detailed coverage analysis

### Writing New Tests

#### Backend Test Pattern
```python
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_service():
    """Fixture for mocked service."""
    service = MagicMock()
    service.async_method = AsyncMock(return_value="result")
    return service

@pytest.mark.asyncio
async def test_processor_success(mock_service):
    """Test successful processing."""
    processor = MyProcessor(mock_service)
    result = await processor.process(data, context)
    assert result["key"] == "expected_value"
    mock_service.async_method.assert_called_once()
```

#### Extension Test Pattern
```typescript
import * as assert from 'assert';
import * as vscode from 'vscode';

suite('My Test Suite', () => {
    test('Should do something', async () => {
        const result = await someFunction();
        assert.strictEqual(result, expectedValue);
    });
});
```

---
For more architectural details, see the documentation in `docs/`.
