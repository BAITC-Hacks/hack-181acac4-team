import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "../../api";
import type { Proposal, ProposalStatus } from "../../types";
import "./proposals.css";

const statusNames: Record<ProposalStatus, string> = {
  submitted: "На рассмотрении",
  accepted: "Принято",
  rejected: "Отклонено"
};

interface ProposalsProps {
  taskId: string;
  mode: "team" | "business";
  teamId?: string;
}

export default function Proposals({ taskId, mode, teamId }: ProposalsProps) {
  const [chosenTeamId, setChosenTeamId] = useState(teamId ?? "");
  const [idea, setIdea] = useState("");
  const [plan, setPlan] = useState("");
  const [timeline, setTimeline] = useState("");
  const [prototypeUrl, setPrototypeUrl] = useState("");
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [decisionId, setDecisionId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadProposals = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setProposals(await api<Proposal[]>(`/tasks/${encodeURIComponent(taskId)}/proposals`));
    } catch {
      setError("Не удалось загрузить предложения.");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (mode === "business") void loadProposals();
  }, [mode, loadProposals]);

  useEffect(() => { setChosenTeamId(teamId ?? ""); }, [teamId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await api<Proposal>(`/tasks/${encodeURIComponent(taskId)}/proposals`, {
        method: "POST",
        body: JSON.stringify({ team_id: chosenTeamId.trim(), idea: idea.trim(), plan: plan.trim(), timeline: timeline.trim(), prototype_url: prototypeUrl.trim() })
      });
      setIdea("");
      setPlan("");
      setTimeline("");
      setPrototypeUrl("");
      setMessage("Предложение отправлено. Можно отправить ещё одно.");
    } catch {
      setError("Не удалось отправить предложение. Проверьте ID команды и поля формы.");
    } finally {
      setBusy(false);
    }
  }

  async function decide(proposalId: string, decision: "accepted" | "rejected") {
    setDecisionId(proposalId);
    setError("");
    setMessage("");
    try {
      const updated = await api<Proposal>(`/proposals/${encodeURIComponent(proposalId)}/decision`, {
        method: "POST",
        body: JSON.stringify({ decision })
      });
      setProposals((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage("Решение сохранено.");
    } catch {
      setError("Не удалось сохранить решение. Повторите попытку.");
    } finally {
      setDecisionId(null);
    }
  }

  return <div className="proposals">
    {mode === "team" ? <form onSubmit={submit}>
      <h3>Предложить решение</h3>
      {!teamId && <label>ID профиля команды
        <input value={chosenTeamId} onChange={(event) => setChosenTeamId(event.target.value)} required placeholder="UUID команды" />
      </label>}
      <label>Идея решения
        <textarea value={idea} onChange={(event) => setIdea(event.target.value)} required minLength={1} />
      </label>
      <label>План работы
        <textarea value={plan} onChange={(event) => setPlan(event.target.value)} required minLength={1} />
      </label>
      <label>Срок
        <input value={timeline} onChange={(event) => setTimeline(event.target.value)} required />
      </label>
      <label>Ссылка на прототип
        <input type="url" value={prototypeUrl} onChange={(event) => setPrototypeUrl(event.target.value)} placeholder="https://..." />
      </label>
      <button type="submit" disabled={busy || !chosenTeamId.trim()}>{busy ? "Отправляем…" : "Отправить предложение"}</button>
    </form> : <section aria-label="Предложения команд">
      <div className="proposals-heading">
        <h3>Предложения команд</h3>
        <button type="button" onClick={() => void loadProposals()} disabled={loading}>Обновить</button>
      </div>
      {loading && <p role="status">Загружаем предложения…</p>}
      {!loading && proposals.length === 0 && !error && <p>Пока нет предложений.</p>}
      <div className="proposals-list">
        {proposals.map((proposal) => <article key={proposal.id}>
          <div className="proposals-heading">
            <strong>Команда {proposal.team_id}</strong>
            <span>{statusNames[proposal.status]}</span>
          </div>
          <p><strong>Идея:</strong> {proposal.idea}</p>
          <p><strong>План:</strong> {proposal.plan}</p>
          <p><strong>Срок:</strong> {proposal.timeline || "Не указан"}</p>
          {proposal.prototype_url && <p><a href={proposal.prototype_url} target="_blank" rel="noreferrer">Открыть прототип</a></p>}
          <div className="proposals-actions">
            <button type="button" onClick={() => void decide(proposal.id, "accepted")} disabled={decisionId !== null}>Принять</button>
            <button type="button" onClick={() => void decide(proposal.id, "rejected")} disabled={decisionId !== null}>Отклонить</button>
          </div>
        </article>)}
      </div>
    </section>}
    {error && <p role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
  </div>;
}
