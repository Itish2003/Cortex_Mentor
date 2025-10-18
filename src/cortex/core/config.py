from pydantic_settings import BaseSettings
from pathlib import Path
import os 

class Settings(BaseSettings): 
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph/vector_db")
    knowledge_graph_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph")
    upstash_url: str = ""
    upstash_token: str = ""
    llm_model: str = "llama3.1:latest"
    llm_api_url: str = "http://localhost:11434/api/generate"


    class Config:
        env_prefix = "CORTEX_"
        env_file = ".env"
        extra = "ignore"   
        