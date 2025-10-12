from pydantic import BaseModel, Field
from typing import Optional, Literal, List,Any,Dict
from datetime import datetime
from cortex.models.events import SourceEvent

from ..utility.utils import get_utc_now

class Insight(BaseModel):
    insight_id:str = Field(..., description="Unique identifier for the insight.")
    source_event_type:str = Field(..., description="Type of the source event (e.g., git_commit, file_change).")
    summary:str = Field(..., description="A brief summary of the insight.")
    patterns: List[str] = Field(default_factory=list, description="List of identified patterns or anomalies.")
    metadata:Dict[str,Any] = Field(default_factory=dict, description="Additional metadata related to the insight.")
    content_for_embedding:str=Field(..., description="Content prepared for embedding generation.")
    source_event:SourceEvent = Field(...,discriminator= "event_type", description="The original event data that generated this insight.")
    timestamp:datetime = Field(default_factory=get_utc_now, description="The timestamp of the insight creation in UTC format.")