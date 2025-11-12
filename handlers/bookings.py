# === МОДУЛЬ ПОЛУЧЕНИЯ ДАННЫХ О ЗАЯВКАХ И БРОНЯХ === 

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_bookings, get_user_booking_by_id, update_booking_status, get_user_bookings
from config import ADMIN_CHAT_ID
import logging
from aiogram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)


router = Router()

# 🎫 Мои брони
@router.message(F.text == '🎫 Мои брони')
async def my_bookings(message: Message):
    try:
        user_id = message.from_user.id
        bookings = await get_user_bookings(user_id)
        
        if bookings:
            # Формируем список с инлайн-кнопками "Отменить"
            for b in bookings:
                text = (
                    f"• <b>Гостиница:</b> {b['hotel_name']}\n"
                    f"<b>Категория номера:</b> {b['room_category']}\n"
                    f"<b>Дата заезда:</b> {b['check_in']}\n"
                    f"<b>Дата выезда:</b> {b['check_out']}\n"
                    f"<b>Статус:</b> {b['status']}"
                )
                
                # Кнопка "Отменить" с callback_data = cancel_booking_{id}
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_booking_{b['id']}")]
                ])
                
                await message.answer(text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer("🎫 У вас пока нет активных бронирований.", parse_mode="Markdown")
            
    except Exception as e:
        logging.error(f"Error fetching bookings: {e}")
        await message.answer("Ошибка загрузки броней. Попробуйте позже.")

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# === ОБРАБОТЧИК ОТМЕНЫ БРОНИРОВАНИЯ ===
@router.callback_query(F.data.startswith("cancel_booking_"))
async def cancel_booking_handler(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[-1])  # получаем ID брони
    user_id = callback.from_user.id
    
    # Проверяем, принадлежит ли бронь пользователю
    booking = await get_user_booking_by_id(booking_id, user_id)
    
    if not booking:
        await callback.answer("❌ Бронирование не найдено или вы не можете его отменить.", show_alert=True)
        return
    
    if booking["status"] == "cancelled":
        await callback.answer("✅ Бронирование уже отменено.", show_alert=True)
        return
    
    # Обновляем статус в БД
    await update_booking_status(booking_id, "cancelled")
    
    # Подтверждение пользователю
    await callback.message.edit_text(
        f"✅ Бронирование в *{booking['hotel_name']}* отменено.\n\n"
        f"Гостиница: {booking['hotel_name']}\n"
        f"Номер: {booking['room_category']}\n"
        f"Даты: {booking['check_in']} — {booking['check_out']}",
        parse_mode="Markdown"
    )
    
    # Уведомление администратору
    try:
        admin_message = (
            "🗑️ <b>БРОНИРОВАНИЕ ОТМЕНЕНО</b>\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'не указан'} (ID: {user_id})\n"
            f"🏨 Гостиница: {booking['hotel_name']}\n"
            f"🛏️ Категория: {booking['room_category']}\n"
            f"📅 Даты: {booking['check_in']} — {booking['check_out']}"
        )
        await bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки администратору при отмене: {e}")
    
    await callback.answer()        