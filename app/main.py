from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="URL Shortener",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
