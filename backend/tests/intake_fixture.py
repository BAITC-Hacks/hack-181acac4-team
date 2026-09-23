from app.ai.client import is_unknown
from app.schemas import TaskFields, Question

class DemoIntake:
    """Offline fixture: preserve source text, ask about users/data/success; never infer facts."""

    def analyze(self, description: str) -> tuple[TaskFields, list[Question]]:
        return TaskFields(context=description), [
            Question(id="q1", text="Кто будет пользоваться решением — ваши сотрудники, клиенты или другие компании?", field_keys=["users"]),
            Question(id="q2", text="Что вы можете предоставить команде для работы: например, таблицы, примеры заказов, описание процесса или существующий код? Если пока ничего нет, так и напишите.", field_keys=["data"]),
            Question(id="q3", text="По каким признакам вы оцените успех?", field_keys=["success_criteria"]),
        ]

    def assemble(self, description: str, questions: list[dict], answers: list[dict]) -> TaskFields:
        values = {"context": description}
        fields = {q["id"]: q["field_keys"][0] for q in questions if q["field_keys"]}
        for answer in answers:
            if is_unknown(answer["text"]):
                continue
            key = fields.get(answer["question_id"])
            if key:
                values[key] = answer["text"]
        return TaskFields(**values)

