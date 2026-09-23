import unittest
from uuid import UUID

from app.schemas import TaskCard
from app.services.scoring import calculate_score


CARD_ID = UUID("10000000-0000-0000-0000-000000000001")
DRAFT_ID = UUID("20000000-0000-0000-0000-000000000001")


def make_card(**changes: str) -> TaskCard:
    values = {
        "id": CARD_ID,
        "draft_id": DRAFT_ID,
        "business_id": "demo-business",
        "status": "confirmed",
    }
    values.update(changes)
    return TaskCard(**values)


class ScoringTests(unittest.TestCase):
    def test_empty_confirmed_card_scores_zero(self) -> None:
        score = calculate_score(make_card())

        self.assertEqual(score.total, 0)
        self.assertEqual(score.level, "draft")
        self.assertEqual(
            set(score.missing_fields),
            {
                "context",
                "need",
                "data",
                "expected_result",
                "success_criteria",
                "constraints",
                "users",
                "contact",
                "interaction_format",
            },
        )

    def test_complete_confirmed_card_scores_one_hundred(self) -> None:
        score = calculate_score(
            make_card(
                context="Сейчас заявки обрабатываются вручную.",
                need="Нужно сократить время обработки.",
                data="Синтетические заявки и статусы.",
                expected_result="Панель с приоритетами.",
                success_criteria="Время обработки меньше 10 минут.",
                constraints="Демо без персональных данных.",
                users="Операторы и руководители.",
                contact="demo-business@example.test",
                interaction_format="Еженедельное демо.",
            )
        )

        self.assertEqual(score.total, 100)
        self.assertEqual(score.level, "priority")
        self.assertEqual(score.missing_fields, [])
        self.assertEqual(score.criteria.context_need.earned, 20)
        self.assertEqual(score.criteria.business_connection.earned, 10)

    def test_unconfirmed_information_never_earns_points(self) -> None:
        score = calculate_score(
            make_card(
                status="editing",
                context="Заполнено AI, но ещё не подтверждено.",
                need="Есть потребность.",
                data="Есть данные.",
                expected_result="Есть результат.",
                success_criteria="Есть метрика.",
                constraints="Есть ограничения.",
                users="Есть пользователи.",
                contact="demo-business@example.test",
                interaction_format="Созвон.",
            )
        )

        self.assertEqual(score.total, 0)
        self.assertEqual(len(score.missing_fields), 9)

    def test_score_grows_after_confirmed_edit(self) -> None:
        weak = calculate_score(make_card(context="Есть ручной процесс.", need="Нужна автоматизация."))
        improved = calculate_score(
            make_card(
                context="Есть ручной процесс.",
                need="Нужна автоматизация.",
                data="Синтетические события процесса.",
                expected_result="Рабочий прототип.",
            )
        )

        self.assertEqual(weak.total, 20)
        self.assertEqual(improved.total, 55)
        self.assertEqual(weak.level, "draft")
        self.assertEqual(improved.level, "workable")
        self.assertGreater(improved.total, weak.total)

    def test_readiness_level_boundaries(self) -> None:
        draft = calculate_score(make_card(data="20", expected_result="15"))
        workable = calculate_score(make_card(data="20", expected_result="15", contact="5"))
        ready = calculate_score(
            make_card(
                context="10",
                need="10",
                data="20",
                expected_result="15",
                success_criteria="15",
                constraints="10",
            )
        )
        priority = calculate_score(
            make_card(
                context="10",
                need="10",
                data="20",
                expected_result="15",
                success_criteria="15",
                constraints="10",
                users="10",
            )
        )

        self.assertEqual((draft.total, draft.level), (35, "draft"))
        self.assertEqual((workable.total, workable.level), (40, "workable"))
        self.assertEqual((ready.total, ready.level), (80, "ready"))
        self.assertEqual((priority.total, priority.level), (90, "priority"))


if __name__ == "__main__":
    unittest.main()
