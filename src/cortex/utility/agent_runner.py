from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from typing import Optional

async def run_standalone_agent(
    agent: BaseAgent,
    prompt: str,
    target_agent_name: Optional[str] = None
) -> str:
    """
    Runs a standalone agent using an in-memory runner and returns the final text result.
    If target_agent_name is provided, it returns the final text result of that specific agent.
    """
    runner = InMemoryRunner(agent=agent)
    result_text = ""
    async for event in runner.run_async(
        user_id="user",
        session_id="session",
        new_message=types.Content(parts=[types.Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            if target_agent_name:
                if event.author == target_agent_name:
                    result_text = "".join([part.text for part in event.content.parts if part.text])
            else:
                result_text = "".join([part.text for part in event.content.parts if part.text])
    return result_text
