import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models
from app.ai.client import AIError, Evidence, OpenAIIntake, grounded_fields
from app.db import Base, get_db
from app.main import app
from app.schemas import ScoreBreakdown


class IntakeFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)

        def database():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = database
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def create_card(self):
        response = self.client.post("/api/drafts?mode=demo", json={"raw_description": "Нужен бот для кофейни"})
        self.assertEqual(response.status_code, 201)
        draft = response.json()
        self.assertEqual(len(draft["questions"]), 3)
        answers = [
            {"question_id": "q1", "text": "Администраторы кофейни"},
            {"question_id": "q2", "text": "не знаю"},
            {"question_id": "q3", "text": "Не терять заказы"},
        ]
        response = self.client.post(f"/api/drafts/{draft['id']}/answers?mode=demo", json={"answers": answers})
        self.assertEqual(response.status_code, 200)
        return draft, response.json(), answers

    def test_flow_confirmation_editing_and_retry(self):
        draft, card, answers = self.create_card()
        card_id = card["id"]
        self.assertEqual(card["data"], "")
        self.assertEqual(card["constraints"], "")
        self.assertEqual(card["users"], "Администраторы кофейни")
        self.assertEqual(self.client.post(f"/api/cards/{card_id}/publish").status_code, 409)
        response = self.client.patch(f"/api/cards/{card_id}", json={"title": "Учёт заказов"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post(f"/api/cards/{card_id}/confirm").json()["status"], "confirmed")
        self.assertEqual(self.client.post(f"/api/cards/{card_id}/publish").json()["status"], "published")
        updated = self.client.patch(f"/api/cards/{card_id}", json={"contact": "demo@example.test"}).json()
        self.assertEqual(updated["status"], "editing")
        self.assertIsNone(updated["score"])
        self.assertEqual(self.client.post(f"/api/cards/{card_id}/publish").status_code, 409)
        retry = self.client.post(f"/api/drafts/{draft['id']}/answers?mode=demo", json={"answers": answers}).json()
        self.assertEqual(retry["id"], card_id)
        self.assertEqual(retry["title"], "Учёт заказов")
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}/card").json()["contact"], "demo@example.test")

    def test_status_cannot_be_spoofed_in_patch(self):
        _, card, _ = self.create_card()
        self.assertEqual(self.client.patch(f"/api/cards/{card['id']}", json={"status": "confirmed"}).status_code, 422)
        self.assertEqual(self.client.patch(f"/api/cards/{card['id']}", json={"title": None}).status_code, 422)

    def test_invalid_answers_keep_draft_retryable(self):
        draft = self.client.post("/api/drafts?mode=demo", json={"raw_description": "Полное описание бизнеса"}).json()
        response = self.client.post(f"/api/drafts/{draft['id']}/answers?mode=demo",
                                    json={"answers": [{"question_id": "wrong", "text": "Ответ"}]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").json()["status"], "collecting")

    def test_provider_error_does_not_save_partial_draft(self):
        with patch("app.ai.client.OpenAIIntake.analyze", side_effect=AIError("Повторите запрос.")):
            response = self.client.post("/api/drafts", json={"raw_description": "Нужен сайт"})
        self.assertEqual(response.status_code, 503)
        with Session(self.engine) as db:
            self.assertEqual(list(db.scalars(select(models.TaskDraft))), [])

    def test_answer_provider_error_preserves_draft(self):
        draft = self.client.post("/api/drafts?mode=demo", json={"raw_description": "Нужен сайт"}).json()
        answers = [{"question_id": q["id"], "text": "Ответ"} for q in draft["questions"]]
        with patch("app.ai.client.OpenAIIntake.assemble", side_effect=AIError("Повторите.")):
            response = self.client.post(f"/api/drafts/{draft['id']}/answers", json={"answers": answers})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").json()["status"], "collecting")

    def test_blank_description_rejected(self):
        self.assertEqual(self.client.post("/api/drafts?mode=demo", json={"raw_description": "   "}).status_code, 422)

    def test_confirm_uses_scoring_contract(self):
        _, card, _ = self.create_card()
        caps = {"context_need": 20, "data": 20, "expected_result": 15, "success_criteria": 15,
                "constraints": 10, "users": 10, "business_connection": 10}
        score = ScoreBreakdown(total=0, level="draft",
                               criteria={k: {"earned": 0, "max_points": v} for k, v in caps.items()},
                               missing_fields=["data"])
        with patch("app.services.intake.calculate_score", return_value=score) as calculate:
            response = self.client.post(f"/api/cards/{card['id']}/confirm")
        self.assertEqual(response.json()["score"]["total"], 0)
        self.assertEqual(calculate.call_args.args[0].status, "confirmed")


class ProviderContractTests(unittest.TestCase):
    def test_fabricated_quote_rejected(self):
        with self.assertRaises(AIError):
            grounded_fields([Evidence(field="constraints", source_id="description", quote="3 недели")],
                            {"description": "Нужен сайт"})

    def test_absent_information_stays_empty(self):
        fields = grounded_fields([Evidence(field="context", source_id="description", quote="Нужен сайт")],
                                 {"description": "Нужен сайт"})
        self.assertEqual(fields.constraints, "")
        self.assertEqual(fields.context, "Нужен сайт")

    def test_incomplete_response_is_retryable(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-not-a-real-key"}), patch("app.ai.client.OpenAI") as provider:
            provider.return_value.__enter__.return_value.responses.parse.return_value = SimpleNamespace(
                status="incomplete", output_parsed=None)
            with self.assertRaises(AIError):
                OpenAIIntake().analyze("Нужен сайт")

    def test_invalid_question_count_is_rejected(self):
        with patch.object(OpenAIIntake, "_parse", return_value=SimpleNamespace(fields=[], questions=[])):
            with self.assertRaises(AIError):
                OpenAIIntake().analyze("Подробное описание")


if __name__ == "__main__":
    unittest.main()
