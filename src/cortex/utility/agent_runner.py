from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from typing import Optional
import uuid

async def run_standalone_agent(
    agent: BaseAgent,
    prompt: str,
    target_agent_name: Optional[str] = None
) -> str:
    """
    Runs a standalone agent using an in-memory runner and returns the final text result.
    If target_agent_name is provided, it returns the final text result of that specific agent.
    """

    # Create the runner (it creates its own InMemorySessionService internally)
    app_name = "Cortex"
    runner = InMemoryRunner(agent=agent, app_name=app_name)

    # Use the runner's session_service to create a session so that both
    # runner and session share the same in-memory backing
    session_id = str(uuid.uuid4())
    user_id = "user"

    session = await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.Content(parts=[types.Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            if target_agent_name:
                if event.author == target_agent_name:
                    result_text = "".join(
                        part.text for part in event.content.parts if part.text
                    )
            else:
                result_text = "".join(
                    part.text for part in event.content.parts if part.text
                )
            
        event_str = str(event)
        
        if "TerminateProcess:" in event_str:
            print("CreateCurationAgent: Kill signal received from Tool. Stopping.")
           
            if not result_text:
                result_text = "Synthesis Completed (Terminated by Tool)"
            
            break

    return result_text