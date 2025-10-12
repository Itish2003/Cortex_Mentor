import requests
from ..core.config import Settings

class LLMService:
    """
    Service for interacting with Large Language Models (LLMs).
    """
    def __init__(self, model: str = Settings().llm_model, api_url: str = Settings().llm_api_url):
        self.model = model
        self.api_url = api_url

    def generate_commit_summary(self,commit_message:str,commit_diff:str)-> str:
        """
        Generates a semantic summary for a given commit using the LLM.
        """
        prompt = f"""Analyze the following git commit and provide a concise, one-sentence semantic summary. Focus on the *intent* and *impact* of the change, not just a list of files. Do not start your response with 'This user' or 'This commit'. Just state the change directly.

            Example: "Refactored authentication module to improve security and performance."

            Commit Message: {commit_message}
            Commit Diff: {commit_diff}

            Semantic Summary:
            """
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.RequestException as e:
            print(f"Error communicating with LLM API: {e}")
            return "No summary available due to LLM error."

    def generate_code_change_summary(self, file_path: str, change_type: str, content: str) -> str:
        """
        Generates a semantic summary for a file change event.
        """
        prompt = f"""
        A file was changed. Analyze the event and provide a concise, one-sentence semantic summary of the change's likely intent or impact.

        File Path: {file_path}
        Change Type: {change_type}
        New Content:
        ```
        {content}
        ```

        Semantic Summary:
        """

        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.RequestException as e:
            print(f"Error calling LLM service for code change: {e}")
            return "Could not generate summary."