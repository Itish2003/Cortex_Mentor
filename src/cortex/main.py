from fastapi import FastAPI
from cortex.services.vector_db_service import VectorDBService
from contextlib import asynccontextmanager

app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Initializing VectorDBService...")
    app_state["vector_db_service"] = VectorDBService()
    print("[Startup] VectorDBService initialized.")
    yield
    print("[Shutdown] Server is shutting down.")

app = FastAPI(
   title="Cortex Mentor Framework",
   version="0.1.0",
   description="The backend server for the agentic framework",
   lifespan=lifespan
)

@app.get("/")
def root():
    vdb = app_state.get("vector_db_service")
    if vdb is None:
        return {"status": "VectorDBService not initialized"}
    try:
        result = vdb.query("test query")
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    return {"status": "ok", "query_result": result}

@app.get("/health",tags=["Health Check"])
def health_check_endpoint():
	"""A simple healthcheck endpoint"""
	return {"status":"ok","message":"health check passed..."}
