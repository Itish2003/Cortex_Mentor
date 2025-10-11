from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from cortex.models.events import GitCommitEvent
from cortex.core.redis import get_redis
from arq import ArqRedis

router = APIRouter()

@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def create_event(event: GitCommitEvent):
    """
    Accepts an event and enqueues it for processing.
    """
    redis: ArqRedis = get_redis()
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available."
        )
    await redis.enqueue_job('process_event_task', event.model_dump())
    return {"message": "Event received and queued for processing."}
