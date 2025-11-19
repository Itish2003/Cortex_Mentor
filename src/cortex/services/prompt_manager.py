from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages loading and rendering Jinja2 templates for prompts.
    """
    def __init__(self):
        # Construct an absolute path to the 'prompts' directory from the project root
        project_root = Path(__file__).parent.parent.parent
        template_folder = project_root / "cortex/prompts"
        logger.info(f"Attempting to load templates from: {template_folder.resolve()}")
        self.env = Environment(loader=FileSystemLoader(str(template_folder)))

    def render(self, template_name: str, **kwargs) -> str:
        """
        Renders a prompt template with the given context.

        Args:
            template_name: The name of the template file to render.
            **kwargs: The variables to inject into the template.

        Returns:
            The rendered prompt as a string.
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
