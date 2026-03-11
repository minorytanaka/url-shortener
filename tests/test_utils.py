from app.utils import generate_short_id


def test_generate_short_id_length():
    """Проверяет что длина ID соответствует переданному параметру."""
    sid = generate_short_id(7)
    assert len(sid) == 7


def test_generate_short_id_unique():
    """Проверяет отсутствие коллизий при генерации 1000 ID."""
    ids = {generate_short_id() for _ in range(1000)}
    assert len(ids) == 1000


def test_generate_short_id_alphabet():
    """Проверяет что ID содержит только буквы и цифры (base62)."""
    sid = generate_short_id(50)
    assert sid.isalnum()
