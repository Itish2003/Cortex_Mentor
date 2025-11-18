import requests
from cortex.core.config import Settings
from google import genai
from typing import Optional
from .prompt_manager import PromptManager
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Large Language Models (LLMs), supporting both local and cloud-based models.
    """
    def __init__(self):
        """
        Initializes the LLMService. The google-genai library is configured automatically
        by the genai.Client() constructor, which looks for the API key in the environment.
        """
        self.settings = Settings()
        self.prompt_manager = PromptManager()
        self._gemini_client = genai.Client()

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generates a response from the specified LLM.

        Args:
            prompt: The prompt to send to the LLM.
            model: The name of the model to use. If not provided, defaults to the local model.

        Returns:
            The generated text from the LLM.
        """
        model_to_use = model or self.settings.llm_model

        if model_to_use.startswith("gemini-"):
            return self._generate_with_gemini(prompt, model_to_use)
        else:
            return self._generate_with_ollama(prompt, model_to_use)

    def _generate_with_gemini(self, prompt: str, model: str) -> str:
        try:
            response = self._gemini_client.models.generate_content(
                model=model,
                contents=prompt
            )
            if response.parts:
                return "".join([part.text for part in response.parts if part.text]).strip()
            return ""
        except Exception as e:
            logger.error(f"Error communicating with Gemini API: {e}")
            return f"No summary available due to Gemini API error: {e}"

    def _generate_with_ollama(self, prompt: str, model: str) -> str:
        try:
            response = requests.post(
                self.settings.llm_api_url,
                json={"model": model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.RequestException as e:
            logger.error(f"Error communicating with local LLM API: {e}")
            return f"No summary available due to local LLM error: {e}"

    def generate_commit_summary(self, commit_message: str, commit_diff: str) -> str:
        """
        Generates a semantic summary for a given commit using the local LLM.
        """
        prompt = self.prompt_manager.render(
            "commit_summary.jinja2",
            commit_message=commit_message,
            commit_diff=commit_diff
        )
        return self.generate(prompt)

    def generate_code_change_summary(self, file_path: str, change_type: str, content: str) -> str:
        """
        Generates a semantic summary for a file change event using the local LLM.
        """
        prompt = self.prompt_manager.render(
            "code_change_summary.jinja2",
            file_path=file_path,
            change_type=change_type,
            content=content
        )
        return self.generate(prompt)