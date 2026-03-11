import pytest
from httpx import AsyncClient
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_shorten_caches_url_in_redis(client: AsyncClient, redis: Redis):
    """POST /shorten сохраняет маппинг short_id - url в Redis."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]
    cached = await redis.get(f"url:{short_id}")
    assert cached == "https://example.com/"


@pytest.mark.asyncio
async def test_redirect_increments_clicks_in_redis(client: AsyncClient, redis: Redis):
    """GET /{short_id} инкрементирует счётчик кликов в Redis."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]
    await client.get(f"/{short_id}", follow_redirects=False)
    await client.get(f"/{short_id}", follow_redirects=False)
    clicks = await redis.get(f"clicks:{short_id}")
    assert int(clicks) == 2


@pytest.mark.asyncio
async def test_redirect_serves_from_cache(client: AsyncClient, redis: Redis):
    """GET /{short_id} берёт URL из Redis без обращения к БД."""
    # Кладём URL напрямую в Redis (без создания записи в БД)
    await redis.set("url:fake123", "https://cached.com")
    resp = await client.get("/fake123", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://cached.com"


@pytest.mark.asyncio
async def test_stats_flushes_redis_clicks_to_db(client: AsyncClient, redis: Redis):
    """GET /stats сбрасывает клики из Redis в PostgreSQL и обнуляет счётчик."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]

    # 5 кликов через Redis
    for _ in range(5):
        await client.get(f"/{short_id}", follow_redirects=False)

    # Запрашиваем статистику клики должны уйти в БД
    resp = await client.get(f"/stats/{short_id}")
    assert resp.json()["clicks"] == 5

    # Счётчик в Redis должен обнулиться после flush
    redis_clicks = await redis.get(f"clicks:{short_id}")
    assert redis_clicks is None


@pytest.mark.asyncio
async def test_stats_accumulates_clicks(client: AsyncClient, redis: Redis):
    """Повторный запрос /stats суммирует новые клики с уже сохранёнными."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]

    # Первая порция 3 клика
    for _ in range(3):
        await client.get(f"/{short_id}", follow_redirects=False)
    resp = await client.get(f"/stats/{short_id}")
    assert resp.json()["clicks"] == 3

    # Вторая порция ещё 2 клика
    for _ in range(2):
        await client.get(f"/{short_id}", follow_redirects=False)
    resp = await client.get(f"/stats/{short_id}")
    assert resp.json()["clicks"] == 5
