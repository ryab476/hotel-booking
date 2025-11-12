# === МОДУЛЬ ПОЛУЧЕНИЯ ДАННЫХ О ГОСТИНИЦАХ ГК ИЗМАЙЛОВО === 

from aiogram import F, Router
from aiogram.types import Message
from database import get_all_hotels
import logging
from aiogram.types import FSInputFile

router = Router()

# 🏨 Выбрать гостиницу
@router.message(F.text == '🏨 Выбрать гостиницу')
async def select_hotel(message: Message):
    try:
        hotels = await get_all_hotels(sort_by="name", desc=False)
        if hotels:
            hotel_list = "\n".join([
                f"• <b>{hotel['name']}</b>\n  📍 {hotel['address'] or 'Адрес не указан'}\n  🔗 <a href='{hotel['description']}'>Подробнее</a>"
                for hotel in hotels
            ])
            caption = f"🏨 <b>Доступные гостиницы:</b>\n\n{hotel_list}"
        else:
            caption = "🏨 Нет доступных гостиниц."
    except Exception as e:
        logging.error(f"Error fetching hotels: {e}")
        caption = "Ошибка загрузки гостиниц."

    # Отправляем сообщение БЕЗ предпросмотра ссылок
    await message.answer(caption, parse_mode="HTML", disable_web_page_preview=True)