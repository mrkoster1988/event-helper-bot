"""Точка входа: python -m bot — поднимает платформы с заданными токенами."""
import logging
import threading
from . import config
from .platforms import telegram, vk, max

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")


def main():
    runners = []
    if config.TELEGRAM_TOKEN:
        runners.append(("telegram", telegram.main))
    if config.VK_TOKEN:
        runners.append(("vk", vk.main))
    if config.MAX_TOKEN:
        runners.append(("max", max.main))
    if not runners:
        log.error("Ни один токен не задан: TELEGRAM_TOKEN / VK_TOKEN / MAX_TOKEN")
        return
    threads = []
    for name, fn in runners:
        t = threading.Thread(target=fn, name=name)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
