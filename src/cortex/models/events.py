from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from ..utility.utils import get_utc_now

class CodeChangeEvent(BaseModel):
   event_type: Literal["file_change"] = "file_change"
   file_path: str = Field(..., description="The path to the file that was changed.")
   content: Optional[str] = Field(None, description="The new content of the file, if applicable.")
   change_type: Literal["added", "modified", "deleted"]
   timestamp: datetime = Field(default_factory=get_utc_now, description="The timestamp of the change in UTC format.")

class GitCommitEvent(BaseModel):
   event_type: Literal["git_commit"] = "git_commit"
   repo_name: str = Field(..., description="The name of the repository.")
   branch_name: str = Field(..., description="The name of the branch.")
   stats: Optional[dict[str, int]] = Field(None, description="The state of the branch before and after the commit.")
   commit_hash: str = Field(..., description="The full SHA hash of the commit.")
   message: Optional[str] = Field(None, description="The full commit message.")
   author_name: Optional[str] = Field(None, description="The name of the commit author.")
   author_email: Optional[str] = Field(None, description="The email of the commit author.")
   timestamp: datetime = Field(..., description="The timestamp of the commit in UTC format.")
   diff: Optional[str] = Field(None, description="The diff of the commit")

SourceEvent = Union[CodeChangeEvent, GitCommitEvent]