from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_hotels
import logging

router = Router()

# 🏨 Выбрать гостиницу
@router.message(F.text == '🏨 Выбрать гостиницу')
async def select_hotel(message: Message):
    try:
        hotels = await get_all_hotels(sort_by="name", desc=False)
        if hotels:
            for hotel in hotels:
                # Создаем инлайн-клавиатуру с одной кнопкой "Открыть сайт"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🌐 Открыть сайт", url=hotel['description'])] # Используем 'description' как URL
                        # Если у вас есть отдельное поле для сайта, например, 'website', используйте его:
                        # [InlineKeyboardButton(text="🌐 Открыть сайт", url=hotel['website'])]
                    ]
                )
                
                # Формируем текст для одного отеля
                hotel_info = f"🏨 <b>{hotel['name']}</b>\n📍 {hotel['address'] or 'Адрес не указан'}"
                
                # Отправляем сообщение с кнопкой для этого отеля
                await message.answer(hotel_info, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer("🏨 Нет доступных гостиниц.")
    except Exception as e:
        logging.error(f"Error fetching hotels: {e}")
        await message.answer("Ошибка загрузки гостиниц.")


