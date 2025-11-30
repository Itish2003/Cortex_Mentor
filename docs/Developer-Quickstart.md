# Developer Quickstart

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.12+** - Backend runtime
2. **Node.js 18+** - VS Code extension development
3. **Redis** - Message queue and Pub/Sub
4. **Ollama** - Local LLM inference
5. **uv** - Python package manager (Poetry-compatible)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd cortex_mentor
```

### 2. Backend Setup

```bash
# Install dependencies using uv
cd cortex_mentor
uv pip install -e .

# Pull required Ollama models
ollama pull nomic-embed-text:v1.5
ollama pull llava-llama3:latest
ollama pull llama3.1:latest
```

### 3. Environment Configuration

Create `cortex_mentor/.env`:

```env
# Google AI (required for synthesis)
GEMINI_API_KEY=your_google_ai_studio_api_key

# Upstash Vector DB (required for public knowledge)
UPSTASH_URL=your_upstash_vector_db_url
UPSTASH_TOKEN=your_upstash_vector_db_token

# Google Cloud Text-to-Speech (optional, uses default credentials)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Redis (optional, defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama (optional, defaults shown)
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. VS Code Extension Setup

```bash
cd cortex_mentor/cortex-vs
npm install
npm run compile
```

### 5. Start Infrastructure

```bash
# Start Redis
brew services start redis

# Verify Ollama is running
ollama list
```

## Running the System

You'll need **4 concurrent terminal sessions**:

### Terminal 1: ARQ Worker (Event Processing)

```bash
cd cortex_mentor
uv run arq src.cortex.workers.WorkerSettings
```

Expected output:
```
14:23:45: Starting worker for 2 functions: comprehension_task, synthesis_task
14:23:45: redis_version=5.0.4 mem_usage=1.2M clients_connected=2
```

### Terminal 2: FastAPI Server (API + WebSocket)

```bash
cd cortex_mentor
uv run uvicorn src.cortex.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 3: VS Code Extension (Development Host)

```bash
cd cortex_mentor/cortex-vs
npm run watch
```

Then press **F5** in VS Code to launch Extension Development Host.

### Terminal 4: Testing (Optional)

```bash
# Test event ingestion
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "git_commit",
    "repo_name": "test-repo",
    "branch_name": "main",
    "commit_hash": "abc123",
    "message": "feat: Add new feature",
    "author_name": "Test User",
    "author_email": "test@example.com",
    "timestamp": "2025-01-15T10:30:00Z",
    "diff": "diff --git a/test.py b/test.py..."
  }'
```

## Development Workflow

### 1. Git Post-Commit Hook (Automatic Event Ingestion)

```bash
# Install the observer
cd observers/git
chmod +x install.sh
./install.sh

# This copies post-commit to .git/hooks/
# Now every commit triggers event ingestion
```

### 2. VS Code Extension Commands

Open Command Palette (`Cmd+Shift+P`):
- `Cortex: Connect` - Establish WebSocket connection
- `Cortex: Disconnect` - Close connection

### 3. Monitoring Logs

Watch ARQ worker logs for pipeline execution:
```bash
tail -f logs/worker.log  # If logging to file
```

Watch FastAPI logs for WebSocket connections:
```bash
# Logs appear in Terminal 2 (uvicorn)
```

## Common Development Tasks

### Adding a New Processor

1. Create processor class in `src/cortex/pipelines/`:

```python
from cortex.pipelines.processors import Processor

class MyNewProcessor(Processor):
    def __init__(self, my_service: MyService):
        self.my_service = my_service
    
    async def process(self, data: dict, context: dict) -> dict:
        # Your processing logic
        result = await self.my_service.do_something(data)
        return result
```

2. Add to pipeline in `src/cortex/workers.py`:

```python
pipeline = Pipeline([
    ExistingProcessor(),
    MyNewProcessor(my_service=my_service),
    AnotherProcessor(),
])
```

### Adding a New ARQ Task

In `src/cortex/workers.py`:

```python
async def my_new_task(ctx: dict, user_id: str, data: dict) -> str:
    """
    ARQ task function.
    ctx contains services injected by WorkerSettings.
    """
    llm_service = ctx['llm_service']
    result = await llm_service.process(data)
    return result

# Register in WorkerSettings
class WorkerSettings:
    functions = [comprehension_task, synthesis_task, my_new_task]
```

### Modifying LLM Prompts

Prompts are Jinja2 templates in `src/cortex/services/prompts/`:

```python
# src/cortex/services/prompts/my_prompt.j2
You are an AI assistant analyzing code changes.

Commit message: {{ commit_message }}
Diff:
{{ diff }}

Generate a concise summary.
```

Use in code:

```python
from cortex.services.prompt_manager import PromptManager

prompt_manager = PromptManager()
rendered = prompt_manager.render('my_prompt.j2', {
    'commit_message': 'feat: Add feature',
    'diff': 'diff --git...'
})
```

### Running Tests

```bash
cd cortex_mentor
pytest tests/ -v
```

### Debugging WebSocket Issues

Check WebSocket connection in VS Code extension:

1. Open DevTools in Extension Development Host
2. Check Console for WebSocket logs
3. Verify `ws://localhost:8000/ws` is reachable

Check backend WebSocket handler:

```python
# src/cortex/main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Add logging here for debugging
```

## Troubleshooting

### Issue: ARQ worker not processing tasks

**Check:**
1. Redis is running: `redis-cli ping` (should return `PONG`)
2. Worker is connected: Check ARQ worker logs for Redis connection
3. Tasks are enqueued: `redis-cli LLEN arq:queue` (should show pending count)

### Issue: Ollama models not found

**Fix:**
```bash
ollama list  # Verify models are pulled
ollama pull nomic-embed-text:v1.5
ollama pull llava-llama3:latest
ollama pull llama3.1:latest
```

### Issue: Google TTS failing

**Check:**
1. `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account JSON
2. Text-to-Speech API enabled in Google Cloud Console
3. Service account has `roles/cloudtexttospeech.user` permission

### Issue: WebSocket connection refused

**Check:**
1. FastAPI server is running on port 8000
2. No firewall blocking localhost:8000
3. VS Code extension setting for WebSocket URL is correct

### Issue: ChromaDB persistence errors

**Fix:**
```bash
# Reset ChromaDB (CAUTION: deletes all vectors)
rm -rf cortex_mentor/data/knowledge_graph/vector_db/
# Restart ARQ worker to recreate collection
```

## Project Structure Quick Reference

```
cortex_mentor/
├── src/cortex/
│   ├── main.py              # FastAPI app entry point
│   ├── workers.py           # ARQ task definitions
│   ├── pipelines/           # Add new processors here
│   ├── services/            # Add new service integrations here
│   ├── models/              # Add new Pydantic models here
│   └── core/config.py       # Modify settings here
├── cortex-vs/
│   ├── src/extension.ts     # VS Code extension entry
│   └── src/ChatViewProvider.ts  # WebSocket client
├── observers/git/           # Git hook installer
├── tests/                   # Add tests here
└── docs/                    # Documentation
```

## Next Steps

1. Read **Architecture.md** for system design overview
2. Read **Backend-Patterns.md** for code patterns and best practices
3. Explore the codebase starting from `src/cortex/main.py`
4. Try making a commit and watching the ARQ worker process it
5. Open VS Code Extension Development Host and connect to backend
