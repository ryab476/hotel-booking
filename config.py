# === КОНФИГУРАЦИОННЫЙ МОДУЛЬ === 

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_HTTP")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))
DATABASE_URL = os.getenv("DATABASE_URL")

# Дополнительные настройки
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "Контактная информация не указана")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Администратор")