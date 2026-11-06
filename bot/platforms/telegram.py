"""Telegram: aiogram 3.x, polling. Общие и админ-команды, рассылка в чат."""
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from .. import config
from .. import core
from ..players import PlayerStore

log = logging.getLogger("telegram")
players = PlayerStore()
_paused = {"flag": False}


async def send_all(text):
    """Рассылка в общий чат: напоминания, ежедневный гайд, !скажи."""
    if _paused["flag"] and text is not None:
        return
    if text is None:
        text = core.daily_text()
    if config.TELEGRAM_CHAT_ID:
        await Bot(config.TELEGRAM_TOKEN).send_message(config.TELEGRAM_CHAT_ID, text)
    else:
        log.warning("TELEGRAM_CHAT_ID не задан — рассылка пропущена")


async def run():
    bot = Bot(config.TELEGRAM_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def on_msg(m: types.Message):
        user_id = m.from_user.id if m.from_user else 0
        raw = (m.text or "").strip()
        msg = raw.lower()

        # админ: !скажи — отправить в общий чат
        if user_id in config.ADMIN_IDS and (msg.startswith("!скажи") or msg.startswith("скажи")):
            body = raw.split(maxsplit=1)[1].strip() if " " in raw else ""
            if body:
                await send_all(body)
                await m.answer("✅ Отправлено в чат!")
            else:
                await m.answer("❌ Используйте: !скажи текст")
            return

        if user_id in config.ADMIN_IDS and msg in ("!пауза", "пауза"):
            _paused["flag"] = True
            await m.answer("⏸️ Рассылка приостановлена")
            return

        if user_id in config.ADMIN_IDS and msg in ("!запуск", "запуск", "старт"):
            _paused["flag"] = False
            await m.answer("▶️ Рассылка возобновлена")
            return

        answer = core.handle(raw, user_id, players)
        if answer:
            await m.answer(answer)

    # ежедневный гайд + напоминания — простая фоновая петля
    async def scheduler_loop():
        sent_keys = set()
        last_daily = None
        while True:
            await asyncio.sleep(30)
            try:
                now = core.now_msk()
                if not _paused["flag"]:
                    from ..data import reminders
                    for key, r in reminders.items():
                        hm = r["time"]
                        if now.strftime("%H:%M") >= hm and (key, now.date()) not in sent_keys:
                            sent_keys.add((key, now.date()))
                            await send_all(r["message"])
                    if now.strftime("%H:%M") >= config.DAILY_TIME and last_daily != now.date():
                        last_daily = now.date()
                        await send_all(None)
            except Exception as e:
                log.error("scheduler: %s", e)

    asyncio.get_running_loop().create_task(scheduler_loop())
    await dp.start_polling(bot)


def main():
    asyncio.run(run())
