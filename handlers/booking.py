# === МОДУЛЬ ПОДАЧИ ЗАЯВКИ НА РАЗМЕЩЕНИЕ === 

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_reply_keyboard
from database import get_all_hotels, get_hotel_by_id, get_room_categories_by_hotel, get_room_category_by_id, create_booking, has_overlapping_booking
from database import get_hotel_id_by_name, get_room_category_id_by_hotel_and_name
from config import ADMIN_CHAT_ID
import re
from datetime import datetime
from aiogram import Bot
from config import BOT_TOKEN
import logging

router = Router()
bot = Bot(token=BOT_TOKEN)

# === FSM СОСТОЯНИЯ ===
class BookingForm(StatesGroup):
    choosing_hotel = State()
    choosing_room = State()
    entering_dates = State()
    confirming = State()

# 📤 Отправить заявку
@router.message(F.text == '📤 Отправить заявку')
async def start_booking_form(message: Message, state: FSMContext):
    hotels = await get_all_hotels()
    
    if not hotels:
        await message.answer("❌ Нет доступных гостиниц.")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=hotel['name'])] for hotel in hotels
        ] + [[KeyboardButton(text="◀️ Отмена")]],
        resize_keyboard=True
    )
    
    await message.answer("🏨 *Выберите гостиницу:*", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BookingForm.choosing_hotel)

# === ОТМЕНА ===
@router.message(F.text == '◀️ Отмена')
async def cancel_booking(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Заявка отменена.", reply_markup=get_main_reply_keyboard)

# === ОБРАБОТЧИК ВЫБОРА ГОСТИНИЦЫ ===
@router.message(BookingForm.choosing_hotel)
async def choose_hotel(message: Message, state: FSMContext):
    hotel_name = message.text
    
    # ИСПОЛЬЗУЕМ ФУНКЦИЮ ИЗ DATABASE, А НЕ ПРЯМОЙ ПУЛ
    hotel_id = await get_hotel_id_by_name(hotel_name)
    
    if hotel_id is None:
        await message.answer("❌ Гостиница не найдена. Попробуйте снова.")
        return
    
    await state.update_data(hotel_id=hotel_id)
    
    room_categories = await get_room_categories_by_hotel(hotel_id)
    
    if not room_categories:
        await message.answer(f"❌ В гостинице *{hotel_name}* нет доступных категорий номеров.", parse_mode="Markdown")
        await state.clear()
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{rc['name']} — {rc['price']} руб.")] for rc in room_categories
        ] + [[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )
    
    await message.answer(f"🛏️ *Выберите категорию номера в гостинице {hotel_name}*", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BookingForm.choosing_room)

# === ОБРАБОТЧИК ВЫБОРА КАТЕГОРИИ НОМЕРА ===
@router.message(BookingForm.choosing_room)
async def choose_room_category(message: Message, state: FSMContext):
    text = message.text
    room_name = text.split(' — ')[0] if ' — ' in text else text
    
    data = await state.get_data()
    hotel_id = data["hotel_id"]
    
    # ИСПОЛЬЗУЕМ ФУНКЦИЮ ИЗ DATABASE, А НЕ ПРЯМОЙ ПУЛ
    room_category_id = await get_room_category_id_by_hotel_and_name(hotel_id, room_name)
    
    if room_category_id is None:
        await message.answer("❌ Категория номера не найдена. Попробуйте снова.")
        return
    
    await state.update_data(room_category_id=room_category_id)
    
    await message.answer(
        "📅 *Введите даты бронирования в формате:\n\n"
        "С 20.11.2025 по 25.11.2025*\n\n"
        "(можно ввести просто даты через пробел или дефис)",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="◀️ Назад")]],
            resize_keyboard=True
        ),
        parse_mode="Markdown"
    )
    await state.set_state(BookingForm.entering_dates)

# === ОБРАБОТЧИК ВВОДА ДАТ ===
@router.message(BookingForm.entering_dates)
async def enter_dates(message: Message, state: FSMContext):
    text = message.text
    dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', text)
    
    if len(dates) < 2:
        await message.answer(
            "❌ Не удалось распознать даты. Пожалуйста, введите в формате:\n\n"
            "*С 20.11.2025 по 25.11.2025*",
            parse_mode="Markdown"
        )
        return
    
    try:
        check_in = datetime.strptime(dates[0], "%d.%m.%Y").date()
        check_out = datetime.strptime(dates[1], "%d.%m.%Y").date()
        
        if check_in >= check_out:
            await message.answer("❌ Дата заезда должна быть раньше даты выезда.")
            return
            
    except ValueError:
        await message.answer("❌ Неверный формат дат. Используйте DD.MM.YYYY (например, 20.11.2025).",
            reply_markup=keyboard, # Применяем клавиатуру
            parse_mode="Markdown")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    # Сохраняем даты в формате YYYY-MM-DD для БД
    await state.update_data(check_in=str(check_in), check_out=str(check_out))
    
    # Показываем подтверждение (в формате DD.MM.YYYY для пользователя)
    data = await state.get_data()
    hotel_info = await get_hotel_by_id(data["hotel_id"])
    room_info = await get_room_category_by_id(data["room_category_id"])
    
    # Преобразуем даты обратно в формат DD.MM.YYYY для отображения
    display_check_in = check_in.strftime("%d.%m.%Y")
    display_check_out = check_out.strftime("%d.%m.%Y")
    
    caption = (
        f"✅ *Подтвердите вашу заявку:*\n\n"
        f"🏨 *{hotel_info['name']}*\n"
        f"🛏️ *{room_info['name']}*\n"
        f"📅 *Даты: {display_check_in} — {display_check_out}*\n\n"
        f"Нажмите ✅ *Подтвердить*, чтобы отправить заявку."
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(caption, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BookingForm.confirming)

@router.message(BookingForm.confirming, F.text == "✅ Подтвердить")
async def confirm_and_save(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    
    # Проверяем, нет ли пересекающихся бронирований
    if await has_overlapping_booking(user.id, data["check_in"], data["check_out"]):
        await message.answer(
            "❌ У вас уже есть бронирование на эти даты!\n"
            "Невозможно создать новое бронирование с пересекающимися датами.",
            reply_markup=get_main_reply_keyboard
        )
        await state.clear()
        return
    
    await create_booking(
        telegram_id=user.id,
        hotel_id=data["hotel_id"],
        room_category_id=data["room_category_id"],
        check_in=data["check_in"],
        check_out=data["check_out"]
    )
    
    hotel_info = await get_hotel_by_id(data["hotel_id"])
    room_info = await get_room_category_by_id(data["room_category_id"])
    
    admin_message = (
        "🚨 <b>НОВАЯ ЗАЯВКА НА БРОНИРОВАНИЕ</b>\n\n"
        f"👤 Пользователь: @{user.username or 'не указан'} (ID: {user.id})\n"
        f"📞 Телефон: {getattr(user, 'phone_number', 'не указан') or 'не указан'}\n"
        f"🏨 Гостиница: {hotel_info['name']}\n"
        f"🛏️ Категория: {room_info['name']}\n"
        f"📅 Даты: {data['check_in']} — {data['check_out']}\n\n"
        "❗ Свяжитесь с клиентом для подтверждения."
    )
    
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки администратору: {e}")
    
    await message.answer(
        "✅ *Заявка успешно отправлена администратору!*\n\n"
        "Ожидайте подтверждения в течение 24 часов.\n\n"
        "Вы можете посмотреть свои заявки в разделе «🎫 Мои брони».",
        reply_markup=get_main_reply_keyboard,
        parse_mode="Markdown"
    )
    
    await state.clear()

# === ОТМЕНА В ПОДТВЕРЖДЕНИИ ===
@router.message(BookingForm.confirming, F.text == "❌ Отмена")
async def cancel_confirm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Заявка отменена.", reply_markup=get_main_reply_keyboard)

# === НАЗАД НА ПРЕДЫДУЩИЕ ШАГИ ===
@router.message(BookingForm.choosing_room, F.text == "◀️ Назад")
async def back_to_hotel_choice(message: Message, state: FSMContext):
    await state.set_state(BookingForm.choosing_hotel)
    await start_booking_form(message, state)

@router.message(BookingForm.entering_dates, F.text == "◀️ Назад")
async def back_to_room_choice(message: Message, state: FSMContext):
    await state.set_state(BookingForm.choosing_room)
    await choose_hotel(message, state)