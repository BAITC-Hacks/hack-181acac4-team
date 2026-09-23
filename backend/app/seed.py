"""Deterministic synthetic data for the five-minute demo.

Run ``python -m app.seed`` from ``backend`` after the database is available.
The loader is idempotent by UUID and never contains real people or contacts.
"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Proposal, TaskCard, TaskDraft, TeamProfile


def _uuid(prefix: int, item: int) -> UUID:
    return UUID(f"{prefix:08d}-0000-0000-0000-{item:012d}")


DRAFT_IDS = [_uuid(10, item) for item in range(1, 6)]
CARD_IDS = [_uuid(20, item) for item in range(1, 6)]
TEAM_IDS = [_uuid(30, item) for item in range(1, 6)]
PROPOSAL_IDS = [_uuid(40, item) for item in range(1, 6)]


SYNTHETIC_DRAFTS: tuple[dict[str, Any], ...] = (
    {
        "id": DRAFT_IDS[0],
        "business_id": "demo-retail",
        "raw_description": "Хотим быстрее разбирать обращения покупателей.",
        "known_fields": {"topic": "Поддержка", "need": "Сократить очередь обращений"},
        "questions": [
            {"id": "retail-users", "text": "Кто сейчас разбирает обращения?", "field_keys": ["users"]},
            {"id": "retail-data", "text": "Какие данные доступны по обращениям?", "field_keys": ["data"]},
            {"id": "retail-success", "text": "Как измерить ускорение?", "field_keys": ["success_criteria"]},
        ],
        "answers": [],
        "status": "collecting",
    },
    {
        "id": DRAFT_IDS[1],
        "business_id": "demo-logistics",
        "raw_description": "Нужен прогноз задержек учебных доставок на синтетических маршрутах.",
        "known_fields": {"topic": "Логистика", "users": "Диспетчеры"},
        "questions": [
            {"id": "log-data", "text": "Какие события маршрута доступны?", "field_keys": ["data"]},
            {"id": "log-result", "text": "Как должен выглядеть прогноз?", "field_keys": ["expected_result"]},
            {"id": "log-limit", "text": "Какие ограничения у демо?", "field_keys": ["constraints"]},
        ],
        "answers": [{"question_id": "log-data", "text": "Синтетические отметки времени и статусы."}],
        "status": "card_created",
    },
    {
        "id": DRAFT_IDS[2],
        "business_id": "demo-learning",
        "raw_description": "Собрать панель прогресса для вымышленной образовательной программы.",
        "known_fields": {"topic": "Образование", "users": "Кураторы программы"},
        "questions": [
            {"id": "edu-context", "text": "Как кураторы работают сейчас?", "field_keys": ["context"]},
            {"id": "edu-metric", "text": "Какая метрика важнее всего?", "field_keys": ["success_criteria"]},
            {"id": "edu-format", "text": "Как часто нужен результат?", "field_keys": ["interaction_format"]},
        ],
        "answers": [],
        "status": "card_created",
    },
    {
        "id": DRAFT_IDS[3],
        "business_id": "demo-energy",
        "raw_description": "Показать аномалии потребления на искусственных показаниях датчиков.",
        "known_fields": {"topic": "Энергетика", "data": "Искусственные почасовые показания"},
        "questions": [
            {"id": "energy-users", "text": "Кто проверяет аномалии?", "field_keys": ["users"]},
            {"id": "energy-action", "text": "Что делать после обнаружения?", "field_keys": ["expected_result"]},
            {"id": "energy-success", "text": "Как оценить качество?", "field_keys": ["success_criteria"]},
        ],
        "answers": [],
        "status": "card_created",
    },
    {
        "id": DRAFT_IDS[4],
        "business_id": "demo-events",
        "raw_description": "Приоритизировать заявки на вымышленное городское мероприятие.",
        "known_fields": {"topic": "Мероприятия", "users": "Координаторы"},
        "questions": [
            {"id": "event-rules", "text": "По каким правилам выбирать заявки?", "field_keys": ["success_criteria"]},
            {"id": "event-data", "text": "Какие поля есть в заявке?", "field_keys": ["data"]},
            {"id": "event-contact", "text": "Кто подтверждает результат?", "field_keys": ["contact"]},
        ],
        "answers": [],
        "status": "card_created",
    },
)


def _score(total: int, level: str, earned: tuple[int, int, int, int, int, int, int], missing: list[str]) -> dict[str, Any]:
    keys = (
        ("context_need", 20),
        ("data", 20),
        ("expected_result", 15),
        ("success_criteria", 15),
        ("constraints", 10),
        ("users", 10),
        ("business_connection", 10),
    )
    return {
        "total": total,
        "level": level,
        "criteria": {
            key: {"earned": points, "max_points": maximum}
            for (key, maximum), points in zip(keys, earned, strict=True)
        },
        "missing_fields": missing,
    }


SYNTHETIC_CARDS: tuple[dict[str, Any], ...] = (
    {
        "id": CARD_IDS[0], "draft_id": DRAFT_IDS[0], "business_id": "demo-retail", "topic": "Поддержка",
        "title": "Очередь обращений", "context": "", "need": "Сократить очередь обращений", "users": "",
        "data": "", "constraints": "", "expected_result": "", "success_criteria": "",
        "contact": "", "interaction_format": "", "status": "editing", "score_total": 0, "score_level": "draft",
        "score": _score(0, "draft", (0, 0, 0, 0, 0, 0, 0), ["data", "expected_result", "success_criteria", "context", "need", "constraints", "users", "contact", "interaction_format"]),
    },
    {
        "id": CARD_IDS[1], "draft_id": DRAFT_IDS[1], "business_id": "demo-logistics", "topic": "Логистика",
        "title": "Прогноз задержек", "context": "Маршруты проверяют вручную", "need": "Предупреждать о риске задержки",
        "users": "Диспетчеры", "data": "Синтетические отметки времени и статусы", "constraints": "Только демо-данные",
        "expected_result": "Список маршрутов с риском", "success_criteria": "", "contact": "", "interaction_format": "",
        "status": "confirmed", "score_total": 75, "score_level": "ready",
        "score": _score(75, "ready", (20, 20, 15, 0, 10, 10, 0), ["success_criteria", "contact", "interaction_format"]),
    },
    {
        "id": CARD_IDS[2], "draft_id": DRAFT_IDS[2], "business_id": "demo-learning", "topic": "Образование",
        "title": "Панель прогресса", "context": "Кураторы сводят отчёты вручную", "need": "Видеть прогресс групп",
        "users": "Кураторы программы", "data": "Синтетические посещения и задания", "constraints": "Обновление раз в сутки",
        "expected_result": "Панель групп", "success_criteria": "Отчёт собирается быстрее 5 минут", "contact": "learning@example.test",
        "interaction_format": "Демо по пятницам", "status": "published", "score_total": 100, "score_level": "priority",
        "score": _score(100, "priority", (20, 20, 15, 15, 10, 10, 10), []),
    },
    {
        "id": CARD_IDS[3], "draft_id": DRAFT_IDS[3], "business_id": "demo-energy", "topic": "Энергетика",
        "title": "Аномалии потребления", "context": "Показания просматривают после смены", "need": "Замечать отклонения раньше",
        "users": "Инженеры смены", "data": "Искусственные почасовые показания", "constraints": "", "expected_result": "",
        "success_criteria": "", "contact": "", "interaction_format": "", "status": "confirmed", "score_total": 50,
        "score_level": "workable", "score": _score(50, "workable", (20, 20, 0, 0, 0, 10, 0), ["expected_result", "success_criteria", "constraints", "contact", "interaction_format"]),
    },
    {
        "id": CARD_IDS[4], "draft_id": DRAFT_IDS[4], "business_id": "demo-events", "topic": "Мероприятия",
        "title": "Приоритет заявок", "context": "", "need": "Быстрее распределять заявки", "users": "Координаторы",
        "data": "", "constraints": "", "expected_result": "", "success_criteria": "", "contact": "events@example.test",
        "interaction_format": "Асинхронные комментарии", "status": "confirmed", "score_total": 30, "score_level": "draft",
        "score": _score(30, "draft", (10, 0, 0, 0, 0, 10, 10), ["data", "expected_result", "success_criteria", "context", "constraints"]),
    },
)


SYNTHETIC_TEAMS: tuple[dict[str, Any], ...] = (
    {"id": TEAM_IDS[0], "name": "Команда Север", "skills": ["Python", "аналитика"], "interests": ["логистика"], "contact": "north@example.test"},
    {"id": TEAM_IDS[1], "name": "Команда Спектр", "skills": ["React", "UX"], "interests": ["образование"], "contact": "spectrum@example.test"},
    {"id": TEAM_IDS[2], "name": "Команда Импульс", "skills": ["ML", "FastAPI"], "interests": ["энергетика"], "contact": "impulse@example.test"},
    {"id": TEAM_IDS[3], "name": "Команда Маяк", "skills": ["продукт", "визуализация"], "interests": ["поддержка"], "contact": "beacon@example.test"},
    {"id": TEAM_IDS[4], "name": "Команда Контур", "skills": ["данные", "тестирование"], "interests": ["мероприятия"], "contact": "contour@example.test"},
)


SYNTHETIC_PROPOSALS: tuple[dict[str, Any], ...] = (
    {"id": PROPOSAL_IDS[0], "task_id": CARD_IDS[1], "team_id": TEAM_IDS[0], "idea": "Правила риска по событиям маршрута", "plan": "Подготовить признаки, API и экран", "timeline": "2 дня", "prototype_url": "https://example.test/prototypes/north", "status": "submitted"},
    {"id": PROPOSAL_IDS[1], "task_id": CARD_IDS[2], "team_id": TEAM_IDS[1], "idea": "Панель с прогрессом групп", "plan": "Собрать макет и подключить синтетические данные", "timeline": "3 дня", "prototype_url": "https://example.test/prototypes/spectrum", "status": "accepted"},
    {"id": PROPOSAL_IDS[2], "task_id": CARD_IDS[3], "team_id": TEAM_IDS[2], "idea": "Детектор отклонений с объяснением", "plan": "Базовая линия, пороги и проверка сценариев", "timeline": "3 дня", "prototype_url": "https://example.test/prototypes/impulse", "status": "submitted"},
    {"id": PROPOSAL_IDS[3], "task_id": CARD_IDS[0], "team_id": TEAM_IDS[3], "idea": "Очередь с прозрачными приоритетами", "plan": "Исследование, прототип и тест на пяти обращениях", "timeline": "2 дня", "prototype_url": "https://example.test/prototypes/beacon", "status": "rejected"},
    {"id": PROPOSAL_IDS[4], "task_id": CARD_IDS[4], "team_id": TEAM_IDS[4], "idea": "Проверяемая таблица правил", "plan": "Согласовать правила и покрыть границы тестами", "timeline": "1 день", "prototype_url": "https://example.test/prototypes/contour", "status": "submitted"},
)


def _add_missing(session: Session, model: type[Any], records: Iterable[dict[str, Any]]) -> int:
    added = 0
    for record in records:
        if session.get(model, record["id"]) is None:
            session.add(model(**record))
            added += 1
    return added


def seed_database(session: Session) -> dict[str, int]:
    """Insert all demo records once and return per-table insertion counts."""
    counts = {
        "drafts": _add_missing(session, TaskDraft, SYNTHETIC_DRAFTS),
        "cards": _add_missing(session, TaskCard, SYNTHETIC_CARDS),
        "teams": _add_missing(session, TeamProfile, SYNTHETIC_TEAMS),
        "proposals": _add_missing(session, Proposal, SYNTHETIC_PROPOSALS),
    }
    session.commit()
    return counts


if __name__ == "__main__":
    with SessionLocal() as database:
        inserted = seed_database(database)
    print(f"Synthetic demo data ready: {inserted}")
