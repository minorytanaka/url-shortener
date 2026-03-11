from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    cache_ttl: int
    short_id_length: int
    redis_max_connections: int = 20

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
