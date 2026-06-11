from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.database import init_db
from routers.leaders import leadersRouter
from routers.users import userRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(userRouter)
app.include_router(leadersRouter)


@app.get("/")
def home():
    return {"message": "hello from task management"}
