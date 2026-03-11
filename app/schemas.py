from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_id: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    short_id: str
    original_url: str
    clicks: int
    created_at: datetime
