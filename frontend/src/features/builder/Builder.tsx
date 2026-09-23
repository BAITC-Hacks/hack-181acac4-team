import { useEffect, useState } from "react";
import { api } from "../../api";
import type { TaskCard, TaskDraft, TaskFields } from "../../types";
import { cardFields, toFields } from "./fields";
import "./builder.css";
import { ScoreBreakdown } from "../scoring";
import Proposals from "../proposals/Proposals";

const STORAGE_KEY = "hackalem-intake";
type Mode = "openai" | "demo";

function remember(id: string, mode: Mode) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ id, mode })); } catch { /* Storage is optional. */ }
}

export default function Builder() {
  const [description, setDescription] = useState("");
  const [mode, setMode] = useState<Mode>("openai");
  const [draft, setDraft] = useState<TaskDraft | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [card, setCard] = useState<TaskCard | null>(null);
  const [values, setValues] = useState<TaskFields | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function showCard(next: TaskCard) {
    setCard(next);
    setValues(toFields(next));
    setConsent(false);
  }

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try { await action(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Не удалось выполнить действие."); }
    finally { setBusy(false); }
  }

  useEffect(() => {
    let cancelled = false;
    let saved: { id: string; mode: Mode } | null = null;
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (value && typeof value.id === "string" && ["openai", "demo"].includes(value.mode)) saved = value;
    } catch { /* A fresh intake still works without local storage. */ }
    if (!saved) return;
    const session = saved;
    setBusy(true);
    void (async () => {
      try {
        const restored = await api<TaskDraft>(`/drafts/${session.id}`);
        const restoredCard = restored.status === "card_created"
          ? await api<TaskCard>(`/drafts/${session.id}/card`) : null;
        if (cancelled) return;
        setDraft(restored);
        setDescription(restored.raw_description);
        setMode(session.mode);
        setAnswers(Object.fromEntries(restored.answers.map(a => [a.question_id, a.text])));
        if (restoredCard) showCard(restoredCard);
      } catch {
        if (!cancelled) setError("Не удалось восстановить задачу. Обновите страницу для повтора или начните новую.");
      } finally { if (!cancelled) setBusy(false); }
    })();
    return () => { cancelled = true; };
  }, []);

  const dirty = !!card && !!values && cardFields.some(({ key }) => values[key] !== card[key]);

  function reset() {
    if ((draft || description) && !window.confirm("Начать новую задачу? Несохранённые изменения будут потеряны.")) return;
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* Optional storage. */ }
    setDraft(null); setCard(null); setValues(null); setAnswers({});
    setDescription(""); setError(""); setNotice(""); setConsent(false);
  }

  async function create() {
    await run(async () => {
      const next = await api<TaskDraft>(`/drafts?mode=${mode}`, {
        method: "POST", body: JSON.stringify({ raw_description: description }),
      });
      setDraft(next);
      setAnswers({});
      remember(next.id, mode);
    });
  }

  async function assemble() {
    if (!draft) return;
    await run(async () => {
      const next = await api<TaskCard>(`/drafts/${draft.id}/answers?mode=${mode}`, {
        method: "POST",
        body: JSON.stringify({
          answers: draft.questions.map(q => ({ question_id: q.id, text: answers[q.id] || "" })),
        }),
      });
      showCard(next);
      remember(draft.id, mode);
    });
  }

  async function save(): Promise<TaskCard> {
    if (!card || !values) throw new Error("Карточка не найдена.");
    if (!dirty) return card;
    const next = await api<TaskCard>(`/cards/${card.id}`, {
      method: "PATCH", body: JSON.stringify(values),
    });
    showCard(next);
    return next;
  }

  async function confirm() {
    if (!consent) return;
    await run(async () => {
      const saved = await save();
      const next = await api<TaskCard>(`/cards/${saved.id}/confirm`, { method: "POST" });
      showCard(next);
      setNotice("Карточка подтверждена. Теперь её можно опубликовать.");
    });
  }

  async function publish() {
    if (!card || dirty) return;
    await run(async () => {
      showCard(await api<TaskCard>(`/cards/${card.id}/publish`, { method: "POST" }));
      setNotice("Карточка опубликована.");
    });
  }

  return (
    <div className="builder" aria-busy={busy}>
      <div className="builder-heading">
        <div>
          <p className="eyebrow">Задача бизнеса</p>
          <h2>{card ? "Проверьте карточку" : draft ? "Уточним три детали" : "С чего начнём?"}</h2>
        </div>
        <button type="button" disabled={busy} onClick={reset}>Новая задача</button>
      </div>
      <ol className="builder-steps" aria-label="Этапы">
        <li aria-current={!draft ? "step" : undefined}>1. Описание</li>
        <li aria-current={draft && !card ? "step" : undefined}>2. Три вопроса</li>
        <li aria-current={card ? "step" : undefined}>3. Карточка</li>
      </ol>

      {error && <div role="alert" className="builder-error">{error} Повторите действие после исправления.</div>}
      {notice && <div role="status" className="builder-notice">{notice}</div>}
      {busy && <p role="status">Обрабатываем запрос… Это может занять до минуты.</p>}

      {!card && (
        <label className="builder-checkbox">
          <input type="checkbox" disabled={busy} checked={mode === "demo"}
            onChange={event => setMode(event.target.checked ? "demo" : "openai")} />
          Деморежим без OpenAI
        </label>
      )}
      {mode === "demo" && <p className="builder-hint">Локальная заглушка: переносит ваш текст дословно и задаёт шаблонные вопросы. AI-анализ отключён.</p>}

      {!draft && <form onSubmit={event => { event.preventDefault(); void create(); }}>
        <label htmlFor="description">Опишите задачу своими словами</label>
        <textarea id="description" rows={7} maxLength={20000} required disabled={busy}
          value={description} onChange={event => setDescription(event.target.value)}
          placeholder="Например: у нашей кофейни заказы приходят в мессенджер и иногда теряются. Хотим упорядочить их обработку." />
        <p className="builder-hint">Укажите то, что уже известно. AI задаст три вопроса даже при подробном описании.</p>
        <button className="builder-primary" disabled={busy || !description.trim()}>Получить три вопроса</button>
      </form>}

      {draft && !card && <form onSubmit={event => { event.preventDefault(); void assemble(); }}>
        <details><summary>Исходное описание</summary><p className="source-text">{draft.raw_description}</p></details>
        {draft.questions.map((question, index) => <div className="builder-field" key={question.id}>
          <label htmlFor={question.id}>{index + 1}. {question.text}</label>
          <textarea id={question.id} rows={3} maxLength={10000} required disabled={busy}
            value={answers[question.id] || ""}
            onChange={event => setAnswers({ ...answers, [question.id]: event.target.value })}
            placeholder="Если сведений пока нет, напишите «не знаю»." />
        </div>)}
        <button className="builder-primary"
          disabled={busy || draft.questions.some(q => !(answers[q.id] || "").trim())}>
          Собрать карточку
        </button>
      </form>}

      {card && values && <>
        <p className="builder-hint">Проверьте каждое поле. Неизвестные сведения оставлены пустыми — их можно заполнить вручную.</p>
        <p className="builder-status">Статус: {dirty || card.status === "editing" ? "требует подтверждения"
          : card.status === "published" ? "опубликована" : "подтверждена"}</p>
        {card.status === "published" && <p className="builder-hint">После сохранения изменений карточку потребуется заново подтвердить и опубликовать.</p>}
        <div className="builder-grid">
          {cardFields.map(({ key, label, hint }) => <div className="builder-field" key={key}>
            <label htmlFor={`card-${key}`}>{label}</label>
            <textarea id={`card-${key}`} rows={key === "title" || key === "topic" ? 2 : 3}
              maxLength={key === "topic" ? 100 : 20000} disabled={busy} value={values[key]}
              placeholder={hint}
              onChange={event => { setValues({ ...values, [key]: event.target.value }); setConsent(false); setNotice(""); }} />
          </div>)}
        </div>
        {card.score && !dirty && <ScoreBreakdown score={card.score} />}
        {(dirty || card.status === "editing") && <label className="builder-checkbox">
          <input type="checkbox" checked={consent} disabled={busy}
            onChange={event => setConsent(event.target.checked)} />
          Я проверил сведения в карточке и подтверждаю их.
        </label>}
        <div className="builder-actions">
          <button disabled={busy || !dirty} onClick={() => void run(async () => { await save(); setNotice("Изменения сохранены."); })}>
            Сохранить изменения
          </button>
          {(dirty || card.status === "editing") && <button className="builder-primary"
            disabled={busy || !consent} onClick={() => void confirm()}>Подтвердить карточку</button>}
          <button className="builder-primary" disabled={busy || dirty || card.status !== "confirmed"}
            onClick={() => void publish()}>{card.status === "published" ? "Опубликовано" : "Опубликовать"}</button>
        </div>
        {card.status === "published" && !dirty && <Proposals key={card.id} taskId={card.id} mode="business" />}
      </>}
    </div>
  );
}
