"""VK: vk_api longpoll. Общие и админ-команды, рассылка, удаление прошлого сообщения."""
import logging
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from .. import config
from .. import core
from ..players import PlayerStore

log = logging.getLogger("vk")
players = PlayerStore()
_last_msg_id = {"id": None}


def _send_all(text):
    if text is None:
        text = core.daily_text()
    if not config.VK_GROUP_ID:
        log.warning("VK_GROUP_ID не задан — рассылка пропущена")
        return
    try:
        resp = _api().messages.send(peer_id=-config.VK_GROUP_ID,
                                    message=text, random_id=0)
        _last_msg_id["id"] = resp
    except Exception as e:
        log.error("send_all: %s", e)


def _delete_last():
    api = _api()
    if _last_msg_id["id"]:
        try:
            api.messages.delete(peer_id=-config.VK_GROUP_ID,
                                delete_for_all=1,
                                cmids=str(_last_msg_id["id"]))
            _last_msg_id["id"] = None
        except Exception as e:
            log.error("delete: %s", e)


def _api():
    session = vk_api.VkApi(token=config.VK_TOKEN)
    return session.get_api()


def main():
    session = vk_api.VkApi(token=config.VK_TOKEN)
    api = session.get_api()
    longpoll = VkLongPoll(session)
    log.info("VK bot started")

    import threading, time
    from ..data import reminders

    _paused = {"flag": False}

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
                        _send_all(r["message"])
                if now.strftime("%H:%M") >= config.DAILY_TIME and last_daily != now.date():
                    last_daily = now.date()
                    _delete_last()
                    _send_all(None)
            except Exception as e:
                log.error("scheduler: %s", e)

    threading.Thread(target=scheduler_loop, name="vk-scheduler", daemon=True).start()

    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
            continue
        user_id = event.user_id
        raw = event.text.strip()
        msg = raw.lower()

        if user_id in config.ADMIN_IDS and msg.startswith(("!скажи", "скажи")):
            body = raw.split(maxsplit=1)[1].strip() if " " in raw else ""
            if body:
                _send_all(body)
                api.messages.send(user_id=event.user_id, message="✅ Отправлено!", random_id=0)
            else:
                api.messages.send(user_id=event.user_id, message="❌ Используйте: !скажи текст", random_id=0)
            continue

        if user_id in config.ADMIN_IDS and msg in ("!пауза", "пауза"):
            _paused["flag"] = True
            api.messages.send(user_id=user_id, message="⏸️ Рассылка приостановлена", random_id=0)
            continue

        if user_id in config.ADMIN_IDS and msg in ("!запуск", "запуск"):
            _paused["flag"] = False
            api.messages.send(user_id=user_id, message="▶️ Рассылка возобновлена", random_id=0)
            continue

        if user_id in config.ADMIN_IDS and msg in ("удалить", "!удалить", "del"):
            _delete_last()
            api.messages.send(user_id=user_id, message="✅ Последнее сообщение чата удалено", random_id=0)
            continue

        answer = core.handle(raw, user_id, players)
        if answer:
            try:
                api.messages.send(user_id=user_id, message=answer, random_id=0)
            except Exception as e:
                log.error("send: %s", e)


if __name__ == "__main__":
    main()
