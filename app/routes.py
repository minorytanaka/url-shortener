from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Link
from app.redis import (
    cache_link,
    get_and_reset_clicks,
    get_cached_url,
    get_redis,
    increment_clicks,
)
from app.schemas import ShortenRequest, ShortenResponse, StatsResponse
from app.utils import generate_short_id

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten_url(
    body: ShortenRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    """
    Создаёт короткую ссылку.
    """

    original_url = str(body.url)
    for _ in range(5):
        short_id = generate_short_id(settings.short_id_length)
        exists = await session.scalar(select(Link.id).where(Link.short_id == short_id))
        if not exists:
            break
    else:
        raise HTTPException(
            status_code=500, detail="Не удалось сгенерировать уникальный идентификатор."
        )
    link = Link(short_id=short_id, original_url=original_url)
    session.add(link)
    await session.commit()
    await cache_link(redis, short_id, original_url)
    base_url = str(request.base_url).rstrip("/")
    return ShortenResponse(
        short_id=short_id,
        short_url=f"{base_url}/{short_id}",
        original_url=original_url,
    )


@router.get("/{short_id}")
async def redirect_to_url(
    short_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    """
    Редирект на исходный URL адрес и увеличение счётчика кликов.
    """

    original_url = await get_cached_url(redis, short_id)
    if original_url:
        await increment_clicks(redis, short_id)
        return RedirectResponse(url=original_url, status_code=307)

    link = await session.scalar(select(Link).where(Link.short_id == short_id))
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена.")
    await cache_link(redis, short_id, link.original_url)
    await increment_clicks(redis, short_id)
    return RedirectResponse(url=link.original_url, status_code=307)


@router.get("/stats/{short_id}", response_model=StatsResponse)
async def get_stats(
    short_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    """
    Получить статистику кликов по сокращённому URL адресу.
    """

    link = await session.scalar(select(Link).where(Link.short_id == short_id))
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена.")

    redis_clicks = await get_and_reset_clicks(redis, short_id)
    if redis_clicks > 0:
        link.clicks += redis_clicks
        await session.commit()

    return StatsResponse(
        short_id=link.short_id,
        original_url=link.original_url,
        clicks=link.clicks,
        created_at=link.created_at,
    )
