"""Игроки: ники и активность. Хранение в players.json.

Счёт активности — по дням (исправляет баг исходного скрипта,
где 100 записей обрезались до 50, а len() считал уникальные минуты).
"""
import json
import os
from datetime import datetime


class PlayerStore:
    def __init__(self, path="players.json"):
        self.path = path
        self.players = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, encoding="utf-8") as f:
                    self.players = json.load(f)
        except Exception:
            self.players = {}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.players, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def touch(self, user_id):
        """Отметить активность игрока: +1 к сегодняшнему дню."""
        sid = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        p = self.players.setdefault(
            sid, {"nick": None, "first_seen": today, "last_seen": today, "days": {}})
        p["last_seen"] = today
        p.setdefault("days", {})[today] = p["days"].get(today, 0) + 1
        if len(p["days"]) > 30:  # храним только 30 последних дней
            p["days"] = dict(sorted(p["days"].items())[-30:])
        self.save()

    def nick(self, user_id):
        return self.players.get(str(user_id), {}).get("nick")

    def display(self, user_id):
        return self.nick(user_id) or f"ID{user_id}"

    def by_nick(self, nick):
        for sid, p in self.players.items():
            if (p.get("nick") or "").lower() == nick.lower():
                return int(sid)
        return None

    def set_nick(self, user_id, nick):
        sid = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        p = self.players.setdefault(
            sid, {"nick": None, "first_seen": today, "last_seen": today, "days": {}})
        old = p.get("nick")
        p["nick"] = nick
        self.save()
        return old

    def top(self, limit=10):
        """Топ по суммарной активности за 30 дней. Только ники."""
        rows = [(p.get("nick"), sum(p.get("days", {}).values()))
                for p in self.players.values() if p.get("nick")]
        rows.sort(key=lambda x: -x[1])
        if not rows:
            return "📊 Пока нет игроков с установленными никами"
        out = ["🏆 ТОП АКТИВНЫХ ИГРОКОВ (за 30 дней):", ""]
        for i, (n, c) in enumerate(rows[:limit], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            out.append(f"{medal} {n} — {c}")
        return "\n".join(out)

    def stats(self, user_id):
        p = self.players.get(str(user_id), {})
        days = p.get("days", {})
        return ("📊 СТАТИСТИКА {nick}\n\n"
                "🎮 Ник: {nick}\n"
                "🆕 Первое обращение: {first}\n"
                "📅 Последнее: {last}\n"
                "🔥 Дней с активностью: {d}").format(
            nick=p.get("nick") or "не установлен",
            first=p.get("first_seen", "—"),
            last=p.get("last_seen", "—"),
            d=len(days))

    def count(self):
        return len(self.players)

    def with_nick(self):
        return sum(1 for p in self.players.values() if p.get("nick"))
