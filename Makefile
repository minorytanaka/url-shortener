.PHONY: dev dev-down prod prod-down test logs migrate lint clean

# Development

dev:  ## Запуск в режиме разработки (hot-reload, порты БД/Redis открыты)
	docker compose up -d --build

dev-down:  ## Остановка dev окружения
	docker compose down

# Production

prod:  ## Запуск в продакшен режиме (только nginx наружу)
	docker compose -f docker-compose.yml up -d --build

prod-down:  ## Остановка prod окружения
	docker compose -f docker-compose.yml down

# Tests

test:  ## Запуск тестов (работает и в dev, и в prod)
	docker compose -f docker-compose.yml exec app pytest -v

# Migrations

migrate: ## Создать новую миграцию (usage: make migrate msg="add users table")
	docker compose exec app sh -c "alembic revision --autogenerate -m '$(msg)'"

# Logs

logs: ## Показать логи всех сервисов
	docker compose logs -f

logs-app: ## Показать логи только приложения
	docker compose logs -f app

# Utils

lint:  ## Запуск линтера
	docker compose exec app ruff check app/ tests/

clean:  ## Удалить все контейнеры, volumes и сети проекта
	docker compose down -v --remove-orphans

help:  ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
