# Pushok Sketch Icons v1 — Игровые события и гайды

Единый фирменный стиль: карандашная бирюзовая линия 24×24, янтарные детали, прозрачный фон, собственные значения вместо копирования Crypto Bot.

## Назначение по действующим функциям

- `schedule`: `pi-calendar`
- `daily_guide`: `pi-book`
- `weekly_guide`: `pi-book`
- `search`: `pi-search`
- `clan`: `pi-users`
- `top`: `pi-chart`
- `notification`: `pi-bell`
- `settings`: `pi-settings`
- `time`: `pi-clock`

SVG: `assets/pushok-icons.svg`. Для будущего веб-интерфейса можно использовать `<svg aria-hidden="true"><use href="/assets/pushok-icons.svg#pi-home"/></svg>` (после настройки маршрута статики).

**Нативные кнопки Telegram:** SVG нельзя отправлять в параметр `icon_custom_emoji_id`. Нужна отдельно зарегистрированная коллекция Telegram Custom Emoji и её реальные идентификаторы; до регистрации сохраняем текстовые кнопки без фиктивных ID. VK/MAX и Mini App — только после проверки доступного API и тестов.

Статус: подготовлен ресурс для внедрения, исходные обработчики и меню не изменены.
