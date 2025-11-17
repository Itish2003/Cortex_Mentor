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
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"
    tts_voice_name: str = "en-US-Neural2-C" 


    class Config:
        env_file = ".env"
        extra = "ignore"   
         
        