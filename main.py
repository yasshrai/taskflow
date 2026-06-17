from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
from database.database import init_db
from routers.leaders import leadersRouter
from routers.users import userRouter
import database.redis_db as redis_module
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    redis_module.redis = Redis.from_url(
        url=os.getenv("REDIS_URL", ""),
        decode_responses=True,
    )
    yield
    await redis_module.redis.aclose()


app = FastAPI(lifespan=lifespan)
app.include_router(userRouter)
app.include_router(leadersRouter)


@app.get("/")
def home():
    return {"message": "hello from task management"}
