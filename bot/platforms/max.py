"""MAX: Bot API (botapi.max.ru). Общие и админ-команды, рассылка."""
import logging
import json
import time
import threading
import urllib.request
from .. import config
from .. import core
from ..players import PlayerStore

log = logging.getLogger("max")
players = PlayerStore()
API = "https://botapi.max.ru"


def api_call(method, payload):
    url = f"{API}/{method}?access_token={config.MAX_TOKEN}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get_updates(cursor=None, timeout=25):
    payload = {"timeout": timeout}
    if cursor:
        payload["updates"] = {"cursor": cursor}
    try:
        return api_call("updates", payload)
    except Exception as e:
        log.error("updates: %s", e)
        return {"updates": {"cursor": cursor, "updates": []}}


def send_all(text):
    if text is None:
        text = core.daily_text()
    if not config.MAX_CHAT_ID:
        log.warning("MAX_CHAT_ID не задан — рассылка пропущена")
        return
    try:
        api_call("messages", {"chat_id": config.MAX_CHAT_ID, "text": text})
    except Exception as e:
        log.error("send_all: %s", e)


def reply(chat_id, text):
    try:
        api_call("messages", {"chat_id": chat_id, "text": text})
    except Exception as e:
        log.error("reply: %s", e)


def main():
    log.info("MAX bot started")
    cursor = None
    _paused = {"flag": False}

    from ..data import reminders

    def scheduler_loop():
        sent_keys = set()
        last_daily = None
        while True:
            time.sleep(30)
            try:
                if _paused["flag"]:
                    continue
                now = core.now_msk()
                for key, r in reminders.items():
                    if now.strftime("%H:%M") >= r["time"] and (key, now.date()) not in sent_keys:
                        sent_keys.add((key, now.date()))
                        send_all(r["message"])
                if now.strftime("%H:%M") >= config.DAILY_TIME and last_daily != now.date():
                    last_daily = now.date()
                    send_all(None)
            except Exception as e:
                log.error("scheduler: %s", e)

    threading.Thread(target=scheduler_loop, name="max-scheduler", daemon=True).start()

    while True:
        data = get_updates(cursor)
        cursor = data.get("updates", {}).get("cursor", cursor)
        for u in data.get("updates", {}).get("updates", []):
            if u.get("update_type") != "message_created":
                continue
            payload = u.get("payload", {})
            msg = payload.get("message", {})
            chat_id = msg.get("chat_id")
            sender = payload.get("sender", {})
            user_id = sender.get("user_id", 0)
            raw = (msg.get("text") or "").strip()
            low = raw.lower()

            if user_id in config.ADMIN_IDS and low.startswith(("!скажи", "скажи")):
                body = raw.split(maxsplit=1)[1].strip() if " " in raw else ""
                send_all(body) if body else reply(chat_id, "❌ Используйте: !скажи текст")
                continue

            if user_id in config.ADMIN_IDS and low in ("!пауза", "пауза"):
                _paused["flag"] = True
                reply(chat_id, "⏸️ Рассылка приостановлена")
                continue

            if user_id in config.ADMIN_IDS and low in ("!запуск", "запуск"):
                _paused["flag"] = False
                reply(chat_id, "▶️ Рассылка возобновлена")
                continue

            answer = core.handle(raw, user_id, players)
            if answer and chat_id:
                reply(chat_id, answer)


if __name__ == "__main__":
    main()
