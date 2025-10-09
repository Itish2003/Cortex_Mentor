# Cortex Mentor

Cortex Mentor is an agentic backend framework for knowledge management and vector search, built with FastAPI, ChromaDB, and Ollama embeddings.

## Features
- **Configurable Settings**: Uses Pydantic's `BaseSettings` for environment-based configuration of ChromaDB and Knowledge Graph paths.
- **Vector Database Service**: Integrates ChromaDB with Ollama local embeddings for document storage and semantic search.
- **FastAPI Application**: Includes a robust startup/shutdown lifecycle and a root endpoint that tests the vector DB connection.

## Project Structure
- `src/cortex/core/config.py`: Application settings and configuration.
- `src/cortex/services/vector_db_service.py`: VectorDBService for managing vector storage and queries.
- `src/cortex/main.py`: FastAPI app with service initialization and test endpoint.

## Usage

### 1. Install dependencies
```zsh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Start Ollama (for local embeddings)
Make sure you have Ollama running locally and the `nomic-embed-text` model available:
```zsh
ollama serve &
ollama pull nomic-embed-text
```

### 3. Run the FastAPI server
```zsh
source .venv/bin/activate
uvicorn src.cortex.main:app --reload
```

### 4. Test the API
Visit [http://localhost:8000/](http://localhost:8000/) to trigger a test query against the vector database.

## Environment Variables
You can override default paths by setting environment variables:
- `CORTEX_CHROMADB_PATH`
- `CORTEX_KNOWLEDGE_GRAPH_PATH`

## Example: Adding and Querying Documents
You can use the `VectorDBService` methods in your own code:
```python
from cortex.services.vector_db_service import VectorDBService
vdb = VectorDBService()
vdb.add_document("doc1", "This is a test document.", {"source": "example"})
results = vdb.query("test document")
```

---
For more details, see the code in `src/cortex/` and the documentation in `docs/`.
