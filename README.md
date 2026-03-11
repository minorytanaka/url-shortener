# Сократитель ссылок - тестовое задание

Микросервис для сокращения ссылок (аналог bitly).

## Live Demo
Сервис развёрнут и доступен для тестирования:
- **API:** http://185.68.247.167:8005
- **Swagger:** http://185.68.247.167:8005/docs

```bash
# Создать короткую ссылку
curl -X POST http://185.68.247.167:8005/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'

# Посмотреть статистику
curl http://185.68.247.167:8005/stats/{short_id}
```

## Нагрузочное тестирование
Тест проводился на сервере 1 vCPU / 1 GB RAM (Ubuntu 24) с помощью `wrk`.

**Редирект (GET /{short_id}) - основная нагрузка:**
```
wrk -t4 -c50 -d30s http://localhost:8005/{short_id}
Requests/sec:    174.81
Latency Avg:     273ms
```

## Стек

- **FastAPI** - фреймворк
- **PostgreSQL** - хранение ссылок и статистики
- **Redis** - кэширование ссылок и счётчиков кликов
- **SQLAlchemy + asyncpg** - асинхронный ORM
- **Alembic** - миграции БД
- **Nginx** - reverse proxy, rate limiting
- **Docker Compose** - оркестрация сервисов
- **pytest + httpx** - тестирование на тестовой PostgreSQL

## Архитектура

```
Client -> Nginx (:8005) -> Uvicorn/FastAPI (:8000) -> PostgreSQL
                                                   -> Redis (кэш)
```

При соотношении Read:Write большинство запросов обслуживаются из Redis без обращения к PostgreSQL:

- `POST /shorten` - создаёт запись в PostgreSQL + кэширует в Redis
- `GET /{short_id}` - берёт URL из Redis (cache hit), инкрементирует счётчик в Redis
- `GET /stats/{short_id}` - сбрасывает накопленные клики из Redis в PostgreSQL

## Быстрый старт

### Требования

- Docker и Docker Compose
- make (опционально)

### Запуск

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd url_shortener

# 2. Создать .env из шаблона
cp .env.example .env

# 3. Запустить
make prod
# или без make:
docker compose -f docker-compose.yml up -d --build

# 4. Проверить
curl -X POST http://localhost:8005/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
```

Swagger-документация: http://localhost:8005/docs

### Запуск тестов

```bash
make test
# или без make:
docker compose -f docker-compose.yml exec app pytest -v
```

### Режим разработки

```bash
make dev
# Включает: hot-reload, порты БД (5433) и Redis (6379) открыты наружу
```

## API

### POST /shorten

Создаёт короткую ссылку.

**Запрос:**
```json
{"url": "https://example.com"}
```

**Ответ (201):**
```json
{
  "short_id": "aB3dE7k",
  "short_url": "http://localhost:8005/aB3dE7k",
  "original_url": "https://example.com/"
}
```

### GET /{short_id}

Редирект (307) на оригинальный URL. Счётчик переходов инкрементируется.

### GET /stats/{short_id}

Статистика переходов.

**Ответ (200):**
```json
{
  "short_id": "aB3dE7k",
  "original_url": "https://example.com/",
  "clicks": 42,
  "created_at": "2026-03-11T12:00:00"
}
```

## Команды (Makefile)

| Команда | Описание |
|---------|----------|
| `make prod` | Запуск в продакшен режиме |
| `make dev` | Запуск для разработки (hot-reload) |
| `make test` | Запуск тестов |
| `make logs` | Логи всех сервисов |
| `make migrate msg="описание"` | Создать миграцию |
| `make lint` | Запуск линтера |
| `make clean` | Удалить контейнеры и volumes |

## Структура проекта

```
url_shortener/
├── app/
│   ├── config.py        # Настройки из .env
│   ├── database.py      # Async SQLAlchemy engine
│   ├── main.py          # FastAPI приложение
│   ├── models.py        # Модель Link
│   ├── redis.py         # Redis кэширование
│   ├── routes.py        # Эндпоинты API
│   ├── schemas.py       # Pydantic схемы
│   └── utils.py         # Генерация short_id
├── alembic/             # Миграции
├── tests/
│   ├── conftest.py      # Фикстуры (тестовая БД)
│   ├── test_api.py      # Интеграционные тесты API
│   ├── test_cache.py    # Тесты Redis-кэширования
│   └── test_utils.py    # Unit-тесты утилит
├── nginx/
│   └── nginx.conf       # Rate limiting + reverse proxy
├── docker-compose.yml           # Продакшен
├── docker-compose.override.yml  # Dev-оверрайды
├── Dockerfile
├── entrypoint.sh
├── Makefile
└── .env.example
```

## Docker Compose: prod vs dev

| | Production | Development |
|---|---|---|
| Команда | `make prod` | `make dev` |
| Hot-reload | Нет | Да |
| Порты БД/Redis | Закрыты | Открыты |
| Код | Внутри образа | Монтируется с хоста |
| Зависимости | Из образа | Переустанавливаются при старте |
