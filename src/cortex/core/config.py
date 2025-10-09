from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings): 
    chromadb_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph/vector_db")
    knowledge_graph_path: str = str(Path(__file__).parent.parent.parent / "data/knowledge_graph")

    class Config:
        env_prefix = "CORTEX_"