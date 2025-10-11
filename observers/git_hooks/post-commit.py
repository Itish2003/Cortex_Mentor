# observers/git_hooks/post-commit.py

import sys
import os
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
        url = os.getenv("CORTEX_API_URL")
        if not url:
            print("[Cortex Observer] Error: CORTEX_API_URL is not set.", file=sys.stderr)
            return

        repo = git.Repo(search_parent_directories=True)
        last_commit = repo.head.commit
        event_payload = get_commit_details(last_commit)
        send_event(event_payload, url)
        print("[Cortex Observer] Successfully sent commit event.")

    except Exception as e:
        print(f"[Cortex Observer] Error: Failed to send commit event. {e}", file=sys.stderr)

if __name__ == "__main__":
    main()