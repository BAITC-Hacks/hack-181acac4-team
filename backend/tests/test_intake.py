import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models
from intake_fixture import DemoIntake
from app.ai.client import get_intake_ai, AIError, Evidence, OpenAIIntake, grounded_fields
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
        app.dependency_overrides[get_intake_ai] = DemoIntake
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def create_card(self):
        response = self.client.post("/api/drafts", json={"raw_description": "Нужен бот для кофейни"})
        self.assertEqual(response.status_code, 201)
        draft = response.json()
        self.assertEqual(len(draft["questions"]), 3)
        answers = [
            {"question_id": "q1", "text": "Администраторы кофейни"},
            {"question_id": "q2", "text": "не знаю"},
            {"question_id": "q3", "text": "Не терять заказы"},
        ]
        response = self.client.post(f"/api/drafts/{draft['id']}/answers", json={"answers": answers})
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
        retry = self.client.post(f"/api/drafts/{draft['id']}/answers", json={"answers": answers}).json()
        self.assertEqual(retry["id"], card_id)
        self.assertEqual(retry["title"], "Учёт заказов")
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}/card").json()["contact"], "demo@example.test")

    def test_status_cannot_be_spoofed_in_patch(self):
        _, card, _ = self.create_card()
        self.assertEqual(self.client.patch(f"/api/cards/{card['id']}", json={"status": "confirmed"}).status_code, 422)
        self.assertEqual(self.client.patch(f"/api/cards/{card['id']}", json={"title": None}).status_code, 422)

    def test_invalid_answers_keep_draft_retryable(self):
        draft = self.client.post("/api/drafts", json={"raw_description": "Полное описание бизнеса"}).json()
        response = self.client.post(f"/api/drafts/{draft['id']}/answers",
                                    json={"answers": [{"question_id": "wrong", "text": "Ответ"}]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").json()["status"], "collecting")

    def test_provider_error_does_not_save_partial_draft(self):
        app.dependency_overrides[get_intake_ai] = OpenAIIntake
        with patch("app.ai.client.OpenAIIntake.analyze", side_effect=AIError("Повторите запрос.")):
            response = self.client.post("/api/drafts", json={"raw_description": "Нужен сайт"})
        self.assertEqual(response.status_code, 503)
        with Session(self.engine) as db:
            self.assertEqual(list(db.scalars(select(models.TaskDraft))), [])

    def test_answer_provider_error_preserves_draft(self):
        draft = self.client.post("/api/drafts", json={"raw_description": "Нужен сайт"}).json()
        answers = [{"question_id": q["id"], "text": "Ответ"} for q in draft["questions"]]
        app.dependency_overrides[get_intake_ai] = OpenAIIntake
        with patch("app.ai.client.OpenAIIntake.assemble", side_effect=AIError("Повторите.")):
            response = self.client.post(f"/api/drafts/{draft['id']}/answers", json={"answers": answers})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").json()["status"], "collecting")

    def test_blank_description_rejected(self):
        self.assertEqual(self.client.post("/api/drafts", json={"raw_description": "   "}).status_code, 422)

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
    def test_data_caveat_overrides_positive_review(self):
        from app.ai.client import SemanticReview, FieldReview
        from app.schemas import TaskFields
        review = SemanticReview(fields=[FieldReview(field="data", keep=True)])
        with patch.object(OpenAIIntake, "_parse", return_value=review):
            fields = OpenAIIntake()._review(TaskFields(data="Пока всё в переписках и тетрадке"), {
                "q2": "Пока всё в переписках и тетрадке. Что из этого сможем передать вашей команде, ещё не решили.",
            })
        self.assertEqual(fields.data, "")

    def test_unrelated_uncertainty_does_not_remove_available_data(self):
        from app.ai.client import data_access_unresolved
        self.assertFalse(data_access_unresolved({"q1": "Передадим таблицу заказов. Сроки ещё не решили."}))
        self.assertTrue(data_access_unresolved({"q1": "Пока не можем предоставить доступ к заказам."}))

    def test_semantic_review_removes_misplaced_facts(self):
        from app.ai.client import SemanticReview, FieldReview
        from app.schemas import TaskFields
        fields = TaskFields(context="Принимаем заказы", need="Не терять заказы",
                            users="Два администратора", data="Телеграм",
                            expected_result="Не терять заказы", interaction_format="Два администратора")
        review = SemanticReview(fields=[FieldReview(field=key, keep=key in {"context", "need", "users"})
                                        for key, value in fields.model_dump().items() if value])
        with patch.object(OpenAIIntake, "_parse", return_value=review):
            result = OpenAIIntake()._review(fields, {"description": "Принимаем заказы"})
        self.assertEqual(result.users, "Два администратора")
        self.assertEqual(result.data, "")
        self.assertEqual(result.expected_result, "")
        self.assertEqual(result.interaction_format, "")

    def test_incomplete_semantic_review_cannot_bypass_validation(self):
        from app.ai.client import SemanticReview
        from app.schemas import TaskFields
        with patch.object(OpenAIIntake, "_parse", return_value=SemanticReview(fields=[])):
            with self.assertRaises(AIError):
                OpenAIIntake()._review(TaskFields(data="Телеграм"), {})

    def test_fabricated_quote_rejected(self):
        fields = grounded_fields([
            Evidence(field="constraints", source_id="description", quote="3 недели"),
            Evidence(field="context", source_id="description", quote="Нужен сайт"),
        ], {"description": "Нужен сайт"})
        self.assertEqual(fields.constraints, "")
        self.assertEqual(fields.context, "Нужен сайт")

    def test_invalid_evidence_is_omitted_without_logging_user_text(self):
        evidence = [
            Evidence(field="users", source_id="q1", quote="Секретный клиент"),
            Evidence(field="users", source_id="q1", quote="клиент"),
            Evidence(field="data", source_id="q2", quote="знаю"),
            Evidence(field="need", source_id="missing-sensitive-id", quote="private"),
            Evidence(field="title", source_id="q1", quote=""),
            Evidence(field="topic", source_id="long", quote="x" * 101),
        ]
        with self.assertLogs("app.ai.client", level="WARNING") as logs:
            fields = grounded_fields(evidence, {"q1": "Секретный клиент", "q2": "Не знаю!", "long": "x" * 101})
        self.assertEqual(fields.users, "Секретный клиент")
        self.assertTrue(all(value == "" for key, value in fields.model_dump().items() if key != "users"))
        output = " ".join(logs.output)
        for secret in ["Секретный", "private", "missing-sensitive-id"]:
            self.assertNotIn(secret, output)
        self.assertIn("reason=unknown_information", output)

    @patch.object(OpenAIIntake, "_review", new=lambda self, fields, sources: fields)
    def test_assembly_keeps_valid_fields_when_model_paraphrases_another(self):
        result = SimpleNamespace(fields=[
            Evidence(field="data", source_id="q1", quote="Instagram, Telegram, Whatsapp"),
            Evidence(field="context", source_id="q2", quote="10 заказов в день"),
            Evidence(field="expected_result", source_id="q3", quote="не знаю"),
        ])
        with patch.object(OpenAIIntake, "_parse", return_value=result):
            fields = OpenAIIntake().assemble("Кондитерская", [], [
                {"question_id": "q1", "text": "Instagram, Telegram, Whatsapp"},
                {"question_id": "q2", "text": "в среднем за день 10 за неделю около 70"},
                {"question_id": "q3", "text": "не знаю"},
            ])
        self.assertEqual(fields.data, "Instagram, Telegram, Whatsapp")
        self.assertEqual(fields.context, "Кондитерская")
        self.assertEqual(fields.expected_result, "")

    def test_formatting_changes_preserve_original_text(self):
        fields = grounded_fields([
            Evidence(field="context", source_id="description", quote="Заказы через мессенджеры"),
        ], {"description": "заказы  через\nмессенджеры"})
        self.assertEqual(fields.context, "заказы  через\nмессенджеры")

    def test_multiple_context_facts_are_preserved(self):
        fields = grounded_fields([
            Evidence(field="context", source_id="description", quote="Кондитерская"),
            Evidence(field="context", source_id="q1", quote="Telegram"),
            Evidence(field="context", source_id="q2", quote="10 заказов"),
        ], {"description": "Кондитерская", "q1": "Telegram", "q2": "10 заказов"})
        self.assertEqual(fields.context, "Кондитерская\nTelegram\n10 заказов")

    @patch.object(OpenAIIntake, "_review", new=lambda self, fields, sources: fields)
    def test_repair_restores_exact_quote_without_accepting_invented_facts(self):
        initial = SimpleNamespace(fields=[Evidence(field="need", source_id="description", quote="Упорядочить заказы")])
        repaired = SimpleNamespace(fields=[
            Evidence(field="need", source_id="description", quote="Хотим упорядочить их обработку"),
            Evidence(field="constraints", source_id="description", quote="Неделя"),
        ])
        with patch.object(OpenAIIntake, "_parse", side_effect=[initial, repaired]) as parse:
            fields = OpenAIIntake().assemble("Хотим упорядочить их обработку", [], [])
        self.assertEqual(parse.call_count, 2)
        self.assertEqual(fields.need, "Хотим упорядочить их обработку")
        self.assertEqual(fields.constraints, "")

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
