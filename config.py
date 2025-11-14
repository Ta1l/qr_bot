from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = getenv("BOT_TOKEN")

# ID админа (можно несколько через запятую)
ADMIN_IDS = [int(id) for id in getenv("ADMIN_IDS", "").split(",") if id]

# Проверки
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

if not ADMIN_IDS:
    print("⚠️ Внимание: ADMIN_IDS не установлены. Результаты не будут отправляться админам.")