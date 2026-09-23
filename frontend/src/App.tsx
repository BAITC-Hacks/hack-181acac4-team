import { useEffect, useState } from "react";
import Builder from "./features/builder/Builder";
import Catalog from "./features/catalog/Catalog";
import Proposals from "./features/proposals/Proposals";
import { api } from "./api";
import type { TaskCard, TeamProfile } from "./types";

type Screen = "business" | "catalog" | "team";

const screens: { id: Screen; label: string }[] = [
  { id: "business", label: "Бизнесу" },
  { id: "catalog", label: "Каталог" },
  { id: "team", label: "Командам" }
];

export default function App() {
  const [screen, setScreen] = useState<Screen>("business");
  const [selectedTask, setSelectedTask] = useState<TaskCard | null>(null);
  const [teams, setTeams] = useState<TeamProfile[]>([]);
  const [teamId, setTeamId] = useState("");
  const [teamError, setTeamError] = useState("");

  useEffect(() => {
    if (screen !== "team") return;
    let active = true;
    setTeamError("");
    api<TeamProfile[]>("/teams").then(result => {
      if (active) setTeams(result);
    }).catch(() => { if (active) setTeamError("Не удалось загрузить команды. Перейдите в каталог и попробуйте снова."); });
    return () => { active = false; };
  }, [screen]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">TaskForce</div>
      </header>

      <main className="content">
        <p className="eyebrow">Платформа бизнес-задач</p>
        <h1>От идеи до команды</h1>
        <p className="intro">Бизнес уточняет задачу, команды предлагают решение, выбор остаётся за бизнесом.</p>

        <nav className="tabs" aria-label="Разделы">
          {screens.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === screen ? "active" : ""}
              onClick={() => setScreen(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <section className="panel">
          <div hidden={screen !== "business"}><Builder /></div>
          {screen === "catalog" && <Catalog onSelectTask={task => { setSelectedTask(task); setScreen("team"); }} />}
          {screen === "team" && <>
            <h2>Предложение команды</h2>
            {!selectedTask ? <p>Выберите задачу в каталоге и нажмите «Откликнуться на задачу».</p> : <>
              <h3>{selectedTask.title || "Без названия"}</h3>
              <label>Ваша команда
                <select value={teamId} onChange={event => setTeamId(event.target.value)}>
                  <option value="">Выберите профиль команды</option>
                  {teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}
                </select>
              </label>
              {teamError && <p role="alert">{teamError}</p>}
              {!teamError && teams.length === 0 && <p>Профилей пока нет. Для демо загрузите тестовые данные по инструкции README.</p>}
              {teamId && <Proposals key={`${selectedTask.id}:${teamId}`} taskId={selectedTask.id} mode="team" teamId={teamId} />}
            </>}
          </>}
        </section>
      </main>
    </div>
  );
}
