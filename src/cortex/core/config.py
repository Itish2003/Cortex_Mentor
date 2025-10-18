from pydantic_settings import BaseSettings
from pathlib import Path
import os 

class Settings(BaseSettings): 
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph/vector_db")
    knowledge_graph_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph")
    upstash_url: str = os.getenv("UPSTASH_URL", "")
    upstash_token: str = os.getenv("UPSTASH_TOKEN", "")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.1:latest")
    llm_api_url: str = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")


    class Config:
        env_prefix = "CORTEX_"  