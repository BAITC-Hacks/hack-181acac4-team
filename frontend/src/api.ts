export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`/api${path}`, {
    ...options,
    headers
  }).catch(() => {
    throw new Error("Не удалось связаться с сервером. Проверьте соединение и повторите запрос.");
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail
      : response.status === 422 ? "Проверьте заполнение полей."
      : "Сервис временно недоступен. Повторите запрос.");
  }

  return response.json() as Promise<T>;
}
