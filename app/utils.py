import secrets
import string

CHARACTERS = string.ascii_letters + string.digits  # base62


def generate_short_id(length: int = 7) -> str:
    """Генерирует случайный короткий идентификатор."""
    return "".join(secrets.choice(CHARACTERS) for _ in range(length))
