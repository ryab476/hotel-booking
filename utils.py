# === МОДУЛЬ УТИЛИТ === 
from aiogram import Bot
import logging

async def notify_admin(bot: Bot, admin_chat_id: int, message: str):
    """
    Отправляет сообщение администратору.
    """
    try:
        await bot.send_message(chat_id=admin_chat_id, text=message)
        logging.info(f"Уведомление админу {admin_chat_id} отправлено: {message[:50]}...") # Логируем первые 50 символов
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления админу {admin_chat_id}: {e}")

def sanitize_miniapp_data_universal(data: dict) -> dict:
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = value.strip()
        elif value is None:
            safe_data[key] = ''
        else:
            safe_data[key] = value
    return safe_data        
