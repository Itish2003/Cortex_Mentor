from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from cortex.api import events
from cortex.core.redis import create_redis_pool, close_redis_pool
from cortex.core.ws_connection_manager import ConnectionManager
import asyncio
import logging

logger = logging.getLogger(__name__)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_redis_pool()
    app.state.redis = pool
    
    # Start Redis Pub/Sub listener in a background task
    app.state.pubsub_task = asyncio.create_task(redis_pubsub_listener(app))
    
    yield
    
    # On shutdown, close Redis pool and cancel Pub/Sub listener
    app.state.pubsub_task.cancel()
    await close_redis_pool(app.state.redis)

app = FastAPI(lifespan=lifespan)

app.include_router(events.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Cortex API is running."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, or handle incoming messages if needed
            # For now, we just expect the client to stay connected
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def redis_pubsub_listener(app: FastAPI):
    redis = app.state.redis
    pubsub = redis.pubsub()
    await pubsub.subscribe("insights_channel")
    logger.info("Subscribed to Redis 'insights_channel'")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = message["data"].decode("utf-8")
                logger.info(f"Received message from Redis: {data}")
                await manager.broadcast(data)
            await asyncio.sleep(0.01)  # Small sleep to prevent busy-waiting
    except asyncio.CancelledError:
        logger.info("Redis Pub/Sub listener task cancelled.")
    except Exception as e:
        logger.error(f"Redis Pub/Sub listener error: {e}", exc_info=True)
    finally:
        await pubsub.unsubscribe("insights_channel")
        logger.info("Unsubscribed from Redis 'insights_channel'.")
