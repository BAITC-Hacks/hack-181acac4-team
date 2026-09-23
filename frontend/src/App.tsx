import { useEffect, useState } from "react";

type Screen = "business" | "catalog" | "team";

const screens: { id: Screen; label: string; heading: string; description: string }[] = [
  {
    id: "business",
    label: "Бизнесу",
    heading: "Опишите вашу задачу",
    description: "Здесь появится конструктор: описание, вопросы AI, карточка и рейтинг."
  },
  {
    id: "catalog",
    label: "Каталог",
    heading: "Бизнес-задачи",
    description: "Здесь появятся опубликованные задачи, сортировка и фильтры."
  },
  {
    id: "team",
    label: "Командам",
    heading: "Предложения команд",
    description: "Здесь появится отправка предложений и решение бизнеса."
  }
];

export default function App() {
  const [screen, setScreen] = useState<Screen>("business");
  const [apiReady, setApiReady] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => setApiReady(response.ok))
      .catch(() => setApiReady(false));
  }, []);

  const active = screens.find((item) => item.id === screen)!;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">HackAlem AI</div>
        <span className={`service-status ${apiReady ? "ready" : ""}`}>
          {apiReady === null ? "Проверяем сервис…" : apiReady ? "Сервис готов" : "Сервис недоступен"}
        </span>
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
          <h2>{active.heading}</h2>
          <p>{active.description}</p>
        </section>
      </main>
    </div>
  );
}
