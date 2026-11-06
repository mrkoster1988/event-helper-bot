"""Конфигурация: токены платформ, чаты рассылки, админы."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0") or 0)
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0") or 0)
MAX_TOKEN = os.getenv("MAX_TOKEN", "")
MAX_CHAT_ID = int(os.getenv("MAX_CHAT_ID", "0") or 0)

ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
TZ = os.getenv("TIMEZONE", "Europe/Moscow")
DAILY_TIME = os.getenv("DAILY_TIME", "09:00")   # ежедневная рассылка гайда
