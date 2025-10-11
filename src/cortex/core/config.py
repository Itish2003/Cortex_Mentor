from pydantic_settings import BaseSettings
from pathlib import Path
import os 

class Settings(BaseSettings): 
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph/vector_db")
    knowledge_graph_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph")
    upstash_url: str = os.getenv("UPSTASH_URL", "")
    upstash_token: str = os.getenv("UPSTASH_TOKEN", "")


    class Config:
        env_prefix = "CORTEX_"