from jinja2 import Environment, FileSystemLoader
import os

class PromptManager:
    """
    Manages loading and rendering Jinja2 templates for prompts.
    """
    def __init__(self, template_folder: str = "src/cortex/prompts"):
        self.env = Environment(loader=FileSystemLoader(template_folder))

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
