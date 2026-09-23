import { useEffect, useState } from "react";
import { api } from "../../api";
import type { ReadinessLevel, ScoreBreakdown, TaskCard } from "../../types";
import "./catalog.css";

const levelNames: Record<ReadinessLevel, string> = {
  draft: "Черновик",
  workable: "Рабочая",
  ready: "Готовая",
  priority: "Приоритетная"
};

const criterionNames: Record<keyof ScoreBreakdown["criteria"], string> = {
  context_need: "Контекст и потребность",
  data: "Данные",
  expected_result: "Ожидаемый результат",
  success_criteria: "Критерии успеха",
  constraints: "Ограничения",
  users: "Пользователи",
  business_connection: "Связь с бизнесом"
};

const fieldNames: Record<string, string> = {
  context: "Контекст",
  need: "Потребность",
  data: "Данные",
  expected_result: "Ожидаемый результат",
  success_criteria: "Критерии успеха",
  constraints: "Ограничения",
  users: "Пользователи",
  contact: "Контакт",
  interaction_format: "Формат взаимодействия"
};

interface CatalogProps {
  onSelectTask?: (task: TaskCard) => void;
}

export default function Catalog({ onSelectTask }: CatalogProps) {
  const [tasks, setTasks] = useState<TaskCard[]>([]);
  const [topic, setTopic] = useState("");
  const [level, setLevel] = useState<ReadinessLevel | "">("");
  const [sort, setSort] = useState<"asc" | "desc">("desc");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams({ sort });
    if (topic.trim()) params.set("topic", topic.trim());
    if (level) params.set("level", level);
    setLoading(true);
    setError("");
    api<TaskCard[]>(`/tasks?${params}`)
      .then((result) => { if (active) setTasks(result); })
      .catch(() => { if (active) setError("Не удалось загрузить каталог. Попробуйте ещё раз."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [topic, level, sort]);

  const selected = tasks.find((task) => task.id === selectedId);

  return (
    <div className="catalog">
      <div className="catalog-filters">
        <label>Тема
          <input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Все темы" />
        </label>
        <label>Уровень готовности
          <select value={level} onChange={(event) => setLevel(event.target.value as ReadinessLevel | "")}>
            <option value="">Все уровни</option>
            {Object.entries(levelNames).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>Рейтинг
          <select value={sort} onChange={(event) => setSort(event.target.value as "asc" | "desc")}>
            <option value="desc">Сначала высокий</option>
            <option value="asc">Сначала низкий</option>
          </select>
        </label>
      </div>

      {loading && <p role="status">Загружаем задачи…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && tasks.length === 0 && <p>Опубликованных задач по этим фильтрам нет.</p>}
      {!loading && !error && <div className="catalog-list">
        {tasks.map((task) => <article key={task.id} className="catalog-card">
          <div className="catalog-card-heading">
            <div>
              <span className="catalog-topic">{task.topic || "Без темы"}</span>
              <h3>{task.title || "Без названия"}</h3>
            </div>
            <strong className="catalog-score">{task.score?.total ?? 0}/100</strong>
          </div>
          <p>{task.need || task.context || "Описание пока не заполнено."}</p>
          <p>Готовность: {levelNames[task.score?.level ?? "draft"]}</p>
          <button type="button" onClick={() => setSelectedId(selectedId === task.id ? null : task.id)}>
            {selectedId === task.id ? "Скрыть подробности" : "Подробнее"}
          </button>
        </article>)}
      </div>}

      {selected && <section className="catalog-detail" aria-label="Подробности задачи">
        <h3>{selected.title || "Без названия"}</h3>
        <dl>
          {([
            ["Контекст", selected.context], ["Потребность", selected.need], ["Пользователи", selected.users],
            ["Данные и материалы", selected.data], ["Ограничения", selected.constraints],
            ["Ожидаемый результат", selected.expected_result], ["Критерии успеха", selected.success_criteria],
            ["Контакт", selected.contact], ["Формат взаимодействия", selected.interaction_format]
          ] as [string, string][]).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || "Не указано"}</dd></div>)}
        </dl>
        {selected.score && <>
          <h4>Как рассчитан рейтинг</h4>
          <ul className="catalog-breakdown">
            {(Object.entries(selected.score.criteria) as [keyof ScoreBreakdown["criteria"], { earned: number; max_points: number }][])
              .map(([key, points]) => <li key={key}>{criterionNames[key]}: {points.earned}/{points.max_points}</li>)}
          </ul>
          <h4>Что ещё нужно уточнить</h4>
          <p>{selected.score.missing_fields.length ? selected.score.missing_fields.map((key) => fieldNames[key] || key).join(", ") : "Все сведения заполнены."}</p>
        </>}
        {onSelectTask && <button type="button" onClick={() => onSelectTask(selected)}>Откликнуться на задачу</button>}
      </section>}
    </div>
  );
}
