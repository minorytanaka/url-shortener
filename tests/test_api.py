import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shorten_creates_link(client: AsyncClient):
    """POST /shorten создаёт короткую ссылку и возвращает 201."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    assert resp.status_code == 201

    data = resp.json()
    assert "short_id" in data
    assert data["original_url"] == "https://example.com/"


@pytest.mark.asyncio
async def test_shorten_invalid_url(client: AsyncClient):
    """POST /shorten с невалидным URL возвращает 422."""
    resp = await client.post("/shorten", json={"url": "not-a-url"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_redirect(client: AsyncClient):
    """GET /{short_id} редиректит на оригинальный URL с кодом 307."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]

    resp = await client.get(f"/{short_id}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    """GET /{short_id} с несуществующим ID возвращает 404."""
    resp = await client.get("/nonexistent", follow_redirects=False)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stats_counts_clicks(client: AsyncClient):
    """GET /stats/{short_id} корректно считает количество переходов."""
    resp = await client.post("/shorten", json={"url": "https://example.com"})
    short_id = resp.json()["short_id"]

    for _ in range(3):
        await client.get(f"/{short_id}", follow_redirects=False)

    resp = await client.get(f"/stats/{short_id}")
    assert resp.status_code == 200
    assert resp.json()["clicks"] == 3


@pytest.mark.asyncio
async def test_stats_not_found(client: AsyncClient):
    """GET /stats/{short_id} с несуществующим ID возвращает 404."""
    resp = await client.get("/stats/nonexistent")
    assert resp.status_code == 404
