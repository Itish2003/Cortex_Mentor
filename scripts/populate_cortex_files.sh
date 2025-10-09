#!/bin/bash
# Script to populate config.py, vector_db_service.py, and main.py as specified

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../src/cortex" && pwd)"

# 1. Populate src/cortex/core/config.py
cat > "$PROJECT_ROOT/core/config.py" << 'EOF'
from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph/vector_db")
    knowledge_graph_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph")

    class Config:
        env_prefix = "CORTEX_"
EOF

# 2. Populate src/cortex/services/vector_db_service.py
cat > "$PROJECT_ROOT/services/vector_db_service.py" << 'EOF'
from cortex.core.config import Settings
import chromadb
from chromadb.utils import embedding_functions

class VectorDBService:
    def __init__(self):
        settings = Settings()
        self.client = chromadb.PersistentClient(path=settings.chromadb_path)
        self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(model_name="nomic-embed-text")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_graph",
            embedding_function=self.embedding_fn
        )

    def add_document(self, doc_id: str, content: str, metadata: dict):
        # Placeholder for adding a document to the collection
        pass

    def query(self, query_text: str, n_results: int = 3):
        # Placeholder for querying the collection
        pass
EOF

# 3. Populate src/cortex/main.py
cat > "$PROJECT_ROOT/main.py" << 'EOF'
from fastapi import FastAPI
from cortex.services.vector_db_service import VectorDBService
from contextlib import asynccontextmanager

app_state = {}

@asynccontextmanager
def lifespan(app: FastAPI):
    print("[Startup] Initializing VectorDBService...")
    app_state["vector_db_service"] = VectorDBService()
    print("[Startup] VectorDBService initialized.")
    yield
    print("[Shutdown] Server is shutting down.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    vdb = app_state.get("vector_db_service")
    if vdb is None:
        return {"status": "VectorDBService not initialized"}
    # Test query (placeholder)
    try:
        result = vdb.query("test query")
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    return {"status": "ok", "query_result": result}
EOF

chmod +x "$0"
echo "Script execution complete. Files have been populated."
