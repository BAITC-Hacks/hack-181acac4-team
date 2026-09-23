import type { ScoreBreakdown as ScoreBreakdownValue } from "../../types";
import "./scoring.css";

const labels = {
  context_need: "Контекст и потребность",
  data: "Данные",
  expected_result: "Ожидаемый результат",
  success_criteria: "Критерии успеха",
  constraints: "Ограничения",
  users: "Пользователи",
  business_connection: "Связь с бизнесом"
} as const;

const fieldHints: Record<string, string> = {
  context: "Опишите текущую ситуацию и проблему.",
  need: "Уточните, что именно нужно бизнесу.",
  data: "Добавьте доступные данные и материалы.",
  expected_result: "Опишите ожидаемый результат.",
  success_criteria: "Добавьте измеримые критерии успеха.",
  constraints: "Укажите сроки, бюджет или другие ограничения.",
  users: "Уточните пользователей решения.",
  contact: "Добавьте контакт представителя бизнеса.",
  interaction_format: "Укажите удобный формат взаимодействия."
};

const levelLabels = {
  draft: "Черновик",
  workable: "Рабочая",
  ready: "Готовая",
  priority: "Приоритетная"
} as const;

interface Props {
  score: ScoreBreakdownValue;
}

export function ScoreBreakdown({ score }: Props) {
  const nextStep = score.missing_fields[0];

  return (
    <section className="score-card" aria-labelledby="score-heading">
      <header>
        <div>
          <p className="score-card__eyebrow">Готовность задачи</p>
          <h3 id="score-heading">{levelLabels[score.level]}</h3>
        </div>
        <strong className="score-card__total">{score.total}/100</strong>
      </header>

      <ul className="score-card__criteria">
        {Object.entries(score.criteria).map(([key, criterion]) => (
          <li key={key}>
            <span>{labels[key as keyof typeof labels]}</span>
            <strong>{criterion.earned}/{criterion.max_points}</strong>
          </li>
        ))}
      </ul>

      {nextStep ? (
        <p className="score-card__hint"><strong>Следующий шаг:</strong> {fieldHints[nextStep]}</p>
      ) : (
        <p className="score-card__hint score-card__hint--complete">Все сведения подтверждены.</p>
      )}
    </section>
  );
}
