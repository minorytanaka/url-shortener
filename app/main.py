from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.redis import close_pool, init_pool
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    await close_pool()
    await engine.dispose()


app = FastAPI(
    title="URL Shortener",
    description="Микросервис для сокращения ссылок.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
