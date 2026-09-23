# HackAlem AI

Мини-сервис для оформления бизнес-задач, прозрачного рейтинга и откликов студенческих команд. Общий контракт и владельцы файлов описаны в [AGENTS.md](AGENTS.md).

## Запуск

1. Если нужен OpenAI, скопируйте `.env.example` в `.env` и впишите `OPENAI_API_KEY`. Не добавляйте `.env` в Git.
2. Запустите `docker compose up --build` из корня репозитория.
3. Откройте интерфейс: <http://localhost:5173>. API: <http://localhost:8000/docs>. Проверка базы и API: <http://localhost:8000/api/health>.

На этом этапе запускается **каркас**. Конструктор, рейтинг, каталог и отклики будут добавлены отдельными задачами ANU-6–ANU-10.

## Структура

- `backend/app/models.py` — таблицы PostgreSQL; `schemas.py` — JSON-контракт API.
- `backend/app/drafts.py`, `cards.py`, `catalog.py`, `proposals.py` — тонкие маршруты FastAPI.
- `backend/app/services/` — бизнес-правила по модулям; `backend/app/ai/` — доступ к OpenAI.
- `frontend/src/types.ts` — типы API; `frontend/src/features/` — экраны по модулям.

Каждый агент берёт задачи только своего владельца в Linear и работает в ветке с номером задачи. После обновления `main` Kojizz заполняет `services/scoring.py`, `seed.py` и свой frontend-модуль; Aslan — каталог, отклики и свои frontend-модули. Anuar подключает готовые модули и проверяет полный сценарий.
