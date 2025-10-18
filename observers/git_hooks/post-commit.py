# observers/git_hooks/post-commit.py

import sys
import os

# This ensures the script can find the 'cortex' module
# by adding the project's 'src' directory to the Python path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import requests
import git
from datetime import datetime, timezone
from typing import Dict, Optional
from cortex.models.events import GitCommitEvent

def get_commit_details(commit: git.Commit) -> GitCommitEvent:
    """
    A pure function to extract data from a Git commit object and
    shape it directly into our Pydantic model.
    
    Args:
        commit: A git.Commit object.

    Returns:
        An instance of the GitCommitEvent Pydantic model.
    """
    repo = commit.repo
    repo_name = os.path.basename(repo.working_dir)
    
    try:
        branch_name = repo.active_branch.name
    except TypeError:
        branch_name = "DETACHED_HEAD"
        
    author_datetime_utc = datetime.fromtimestamp(commit.authored_date, tz=timezone.utc)

    stats_dict: Optional[Dict[str, int]] = None
    diff_text: Optional[str] = None

    if commit.parents:
        parent = commit.parents[0]
        diff_text = repo.git.diff(parent, commit)
        commit_stats = commit.stats.total
        stats_dict = {
            "files_changed": commit_stats.get("files", 0),
            "insertions": commit_stats.get("insertions", 0),
            "deletions": commit_stats.get("deletions", 0),
        }
    else:
        diff_text = repo.git.show(commit.hexsha)

    
    raw_message = commit.message 
    if isinstance(raw_message, bytes):
        message_str = raw_message.decode('utf-8', errors='replace')
    else:
        message_str = str(raw_message)

    # Use the Pydantic model to construct and validate the event data.
    # This guarantees the data shape is correct.
    return GitCommitEvent(
        repo_name=repo_name,
        branch_name=branch_name,
        stats=stats_dict,
        commit_hash=commit.hexsha,
        message=message_str,
        author_name=commit.author.name,
        author_email=commit.author.email,
        timestamp=author_datetime_utc,
        diff=diff_text,
    )

def send_event(event: GitCommitEvent, url: str) -> None:
    """
    An impure function with a single responsibility: send the event.
    It now takes the Pydantic model instance directly.
    """
    # .model_dump_json() is the canonical way to serialize a Pydantic model to JSON
    response = requests.post(
        url,
        data=event.model_dump_json(),
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    response.raise_for_status()

def main() -> None:

    """

    The main orchestrator of the script.

    """

    try:

        # Read the URL from the git config instead of the environment

        repo = git.Repo(search_parent_directories=True)

        # 1. Get the raw value from the config. It could be any type.
        raw_url = repo.config_reader().get_value("cortex", "api-url")

        # 2. Explicitly convert the raw value to a string, or None if it's missing.
        #    This guarantees the type for the rest of the function.
        url = str(raw_url) if raw_url else None

        

        if not url:

            # Update the error message

            print("[Cortex Observer] Error: Cortex API URL not set in git config.", file=sys.stderr)

            print("[Cortex Observer] Run: git config --local cortex.api-url \"http://127.0.0.1:8000/api/events\"", file=sys.stderr)

            return



        last_commit = repo.head.commit



        event_payload = get_commit_details(last_commit)



        send_event(event_payload, url)



        print("[Cortex Observer] Successfully sent commit event.")



    except Exception as e:

        print(f"[Cortex Observer] Error: Failed to send commit event. {e}", file=sys.stderr)

if __name__ == "__main__":
    main()