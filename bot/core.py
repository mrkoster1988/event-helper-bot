"""Ядро: расписание, гайд, тексты ответов. Платформенно-независимо."""
from datetime import datetime
from zoneinfo import ZoneInfo
from . import config
from .data import events, reminders, faq
from .players import PlayerStore

TZ = ZoneInfo(config.TZ)
DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
GAME = "Tiles Survive!"


def _m(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def now_msk():
    return datetime.now(TZ)


def covers(ev, t):
    s, e = _m(ev["start"]), _m(ev["end"])
    return (t >= s or t < e) if e <= s else (s <= t < e)


def current_event():
    t = now_msk().hour * 60 + now_msk().minute
    for ev in events["main"]:
        if covers(ev, t):
            return ev
    return None


def next_event():
    t = now_msk().hour * 60 + now_msk().minute
    best, bd = None, 10 ** 9
    for ev in events["main"]:
        if covers(ev, t):
            continue
        d = (_m(ev["start"]) - t) % 1440
        if d < bd:
            bd, best = d, ev
    return best, bd


def fmt_points(n):
    return f"{n:,}".replace(",", " ") + " очков"


def rewards_table(ev, limit=8):
    rows = sorted(ev["rewards"], key=lambda r: -r[1])[:limit]
    return "\n".join(f"• {name} — {fmt_points(pts)}" for name, pts in rows)


def menu_text(name=""):
    cur = current_event()
    nxt, mins = next_event()
    lines = [f"🎮 Event Helper — трекер событий {GAME}", ""]
    if name:
        lines = [f"👋 Привет, {name}!", ""] + lines
    if cur:
        lines.append(f"🟢 Сейчас: {cur['title']} ({cur['start']}–{cur['end']} МСК)")
    else:
        lines.append("⚪ Сейчас активного окна нет")
    if nxt:
        h, m = divmod(mins, 60)
        lines.append(f"⏳ Далее: {nxt['title']} в {nxt['start']} МСК (через {h} ч {m} мин)")
    lines += ["", "📌 КОМАНДЫ:",
              "• /schedule — расписание на сутки",
              "• /allday — события на весь день",
              "• /guide — гайд на сегодня",
              "• /week — гайд на всю неделю",
              "• /overlap — окна пересечений",
              "• !ник Имя — установить игровой ник",
              "• !топ — топ активных",
              "• !я — моя статистика"]
    lines += ["", "❓ Быстрые ответы: " + ", ".join(faq.keys())]
    lines += ["", "👑 Админ: !скажи текст, !пауза, !запуск, !статус, !статистика, !админы"]
    return "\n".join(lines)


def schedule_text():
    t = now_msk().hour * 60 + now_msk().minute
    out = ["⏰ Расписание (МСК):", ""]
    for ev in events["main"]:
        mark = "🟢" if covers(ev, t) else "•"
        out.append(f"{mark} {ev['start']}–{ev['end']} — {ev['title']} ({ev['actions']} действий)")
    return "\n".join(out)


def event_text(title):
    for ev in events["main"]:
        if ev["title"] == title:
            return (f"⏰ {ev['start']}–{ev['end']} МСК — {ev['title']}\n"
                    f"Действий за окно: {ev['actions']}\n\nНаграды:\n{rewards_table(ev)}")
    return None


def allday_text():
    out = ["📋 События на весь день:", ""]
    for ev in events["allday"]:
        top = max(ev["rewards"], key=lambda r: r[1])
        out.append(f"▪️ {ev['title']} — {ev['actions']} действий, топ: {top[0]} ({fmt_points(top[1])})")
    return "\n".join(out)


def guide_text(day=None):
    d = day if day is not None else now_msk().weekday()
    g = events["guide"].get(d)
    if not g:
        return "На этот день гайда нет."
    name, spend, keep, econ = g
    return (f"{name}\n\n"
            f"💰 ТРАТИМ:\n{spend}\n\n"
            f"🏦 КОПИМ (не трогаем):\n{keep}\n\n"
            f"✂️ ЭКОНОМИМ:\n{econ}")


def week_text():
    out = ["📅 ГАЙД НА НЕДЕЛЮ:", ""]
    for d in range(7):
        g = events["guide"].get(d)
        if g:
            out.append(f"▪️ {g[0]}")
    out += ["", "Подробно: /guide (сегодня) или !день пн/вт/ср/чт/пт/сб/вс"]
    return "\n".join(out)


def overlap_text():
    out = ["🔥 Пересечения: основное окно + дневное событие", ""]
    for ev in events["main"]:
        if any(a["title"] == ev["title"] for a in events["allday"]):
            out.append(f"• {ev['start']}–{ev['end']} — {ev['title']}: и основное, и дневное")
    return "\n".join(out)


def daily_text():
    """Ежедневная рассылка: дата + гайд на сегодня."""
    now = now_msk()
    return f"📅 {now.strftime('%d.%m.%Y')} — {DAYS_RU[now.weekday()]}\n\n{guide_text(now.weekday())}"


DAY_ALIASES = {"пн": 0, "понедельник": 0, "вт": 1, "вторник": 1, "ср": 2, "среда": 2,
               "чт": 3, "четверг": 3, "пт": 4, "пятница": 4, "сб": 5, "суббота": 5,
               "вс": 6, "воскресенье": 6}


def handle(text, user_id, players: PlayerStore):
    """Единый обработчик команд для всех платформ."""
    raw = (text or "").strip()
    msg = raw.lower()
    is_admin = user_id in config.ADMIN_IDS
    players.touch(user_id)

    if msg in ("/start", "start", "начать", "меню", "help", "/help", "привет", "команды"):
        return menu_text(players.display(user_id))

    if msg in ("/schedule", "schedule", "расписание"):
        return f"{schedule_text()}\n\n{guide_text()}"

    if msg in ("/allday", "allday", "день"):
        return allday_text()

    if msg in ("/guide", "guide", "гайд"):
        return guide_text()

    if msg in ("/week", "week", "неделя"):
        return week_text()

    if msg in ("/overlap", "overlap", "пересечения"):
        return overlap_text()

    if msg.startswith("!день ") or msg.startswith("день "):
        key = msg.split(maxsplit=1)[1].strip()
        if key in DAY_ALIASES:
            return guide_text(DAY_ALIASES[key])
        return "❓ Не понял день. Примеры: !день пн, !день сб"

    # ---- ники ----
    if raw.startswith("!ник ") or raw.startswith("/ник "):
        new_nick = raw.split(maxsplit=1)[1].strip()
        if not (2 <= len(new_nick) <= 25):
            return "❌ Ник должен быть от 2 до 25 символов"
        existing = players.by_nick(new_nick)
        if existing and existing != user_id:
            return f"❌ Ник '{new_nick}' уже занят!"
        old = players.set_nick(user_id, new_nick)
        return f"✅ Ник изменён: {old} → {new_nick}" if old else f"✅ Привет, {new_nick}!"

    if msg in ("!ник", "/ник", "мой ник"):
        nick = players.nick(user_id)
        return f"🎮 Твой игровой ник: {nick}" if nick else "❌ Нет ника. Установи: !ник ТвойНик"

    if msg in ("!топ", "/топ", "топ", "топ игроков"):
        return players.top()

    if msg in ("!я", "/я", "моя статистика"):
        return players.stats(user_id)

    if msg in ("/get_id", "мой id", "id", "!id"):
        return f"🔑 Твой ID: {user_id}\n🎮 Ник: {players.nick(user_id) or 'не установлен'}"

    # ---- FAQ ----
    if msg in faq:
        return faq[msg]

    # ---- админ ----
    if is_admin:
        if msg in ("!админы", "админы"):
            return "👑 АДМИНИСТРАТОРЫ:\n" + "\n".join(f"• ID {a}" for a in sorted(config.ADMIN_IDS))
        if msg in ("!статус", "статус"):
            from .data import reminders as _r
            jobs = "\n".join(f"⏰ {v['time']} — {k}" for k, v in _r.items())
            jobs += f"\n📅 {config.DAILY_TIME} — ежедневный гайд"
            return (f"📊 СТАТУС БОТА\n\n"
                    f"✅ Работает\n"
                    f"⏰ Часовой пояс: {config.TZ}\n"
                    f"📅 Время: {now_msk().strftime('%H:%M:%S')}\n"
                    f"👑 Админов: {len(config.ADMIN_IDS)}\n"
                    f"🎮 Игроков с никами: {players.with_nick()}\n"
                    f"👥 Всего игроков: {players.count()}\n\n"
                    f"Отложенные задачи:\n{jobs}")
        if msg in ("!статистика", "статистика", "статистика бота"):
            return (f"📊 СТАТИСТИКА:\n\n"
                    f"👥 Всего игроков: {players.count()}\n"
                    f"🎮 С никами: {players.with_nick()}\n\n"
                    f"{players.top()}")

    # ---- название события ----
    ev_text = event_text(raw)
    if ev_text:
        return ev_text

    return ("🤔 Не понял команду. Напиши «меню» — покажу всё.\n"
            "Можно и название события: «Титан», «Шеф Коллекция»...")
