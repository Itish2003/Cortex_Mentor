from fastapi import FastAPI
from contextlib import asynccontextmanager
from cortex.api import events
from cortex.core.redis import create_redis_pool, close_redis_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_redis_pool()
    yield
    await close_redis_pool()

app = FastAPI(lifespan=lifespan)

app.include_router(events.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Cortex API is running."}
