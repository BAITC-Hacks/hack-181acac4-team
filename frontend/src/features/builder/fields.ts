import type { TaskFields } from "../../types";

export const cardFields: { key: keyof TaskFields; label: string; hint: string }[] = [
  { key: "title", label: "Название", hint: "Краткое название задачи" },
  { key: "topic", label: "Тема", hint: "Например: автоматизация, аналитика, web" },
  { key: "context", label: "Контекст", hint: "Как сейчас устроена работа бизнеса" },
  { key: "need", label: "Проблема / потребность", hint: "Что нужно изменить и почему" },
  { key: "users", label: "Пользователи", hint: "Кто будет пользоваться решением" },
  { key: "data", label: "Данные и материалы", hint: "Что доступно и как получить доступ" },
  { key: "constraints", label: "Ограничения", hint: "Сроки, технологии, ресурсы; если ограничений нет, укажите это" },
  { key: "expected_result", label: "Ожидаемый результат", hint: "Что команда должна передать бизнесу" },
  { key: "success_criteria", label: "Критерии успеха", hint: "Как проверить, что задача решена" },
  { key: "contact", label: "Контакт бизнеса", hint: "Как связаться с представителем бизнеса" },
  { key: "interaction_format", label: "Формат взаимодействия", hint: "Канал, частота встреч и обратной связи" },
];

export function toFields(card: TaskFields): TaskFields {
  return Object.fromEntries(cardFields.map(({ key }) => [key, card[key]])) as unknown as TaskFields;
}
