import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, WebAppInfo  # ← добавлен WebAppInfo
)
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))
MINI_APP_URL=os.getenv("MINI_APP_HTTP")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === ЗАГРУЗКА ГОСТИНИЦ ИЗ ФАЙЛА ===
HOTELS_FILE = "hotels.json"

def load_hotels():
    if os.path.exists(HOTELS_FILE):
        try:
            with open(HOTELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Ошибка загрузки hotels.json: {e}")
            return {}
    else:
        default_hotels = {
            "Альфа": {
                "Стандарт": {"price": "4000 руб/ночь", "info": "Номер по умолчанию"}
            }
        }
        with open(HOTELS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_hotels, f, ensure_ascii=False, indent=2)
        return default_hotels

HOTELS = load_hotels()

BOOKINGS_FILE = "bookings.json"

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Ошибка загрузки бронирований: {e}")
            return {}
    return {}

def save_bookings(bookings):
    try:
        with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(bookings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

user_bookings = load_bookings()

# === КОНТАКТ АДМИНА ===
ADMIN_PHONE = "+7 (999) 123-45-67"
ADMIN_NAME = "Администратор сети гостиниц"

# === URL MINI APP (ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ!) ===
#MINI_APP_URL = "https://ваш-сайт.рф/"  # ← ЗАМЕНИТЕ НА РЕАЛЬНЫЙ HTTPS URL

# === КЛАВИАТУРЫ ===

def get_main_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏨 Выбрать гостиницу", callback_data="select_hotel"),
            InlineKeyboardButton(text="📤 Отправить заявку", callback_data="book_start")
        ],
        [
            InlineKeyboardButton(
                text="📅 Забронировать (Mini App)",
                web_app=WebAppInfo(url=MINI_APP_URL)
            ),
            InlineKeyboardButton(text="🎫 Мои брони", callback_data="show_my_booking")
        ],
        [
            InlineKeyboardButton(text="📞 Связаться с админом", callback_data="send_admin_contact"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

def get_hotel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=hotel, callback_data=f"hotel_{hotel}") for hotel in HOTELS],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

def get_category_keyboard(hotel: str):
    if hotel not in HOTELS:
        return get_back_keyboard()
    categories = HOTELS[hotel]
    buttons = [[InlineKeyboardButton(text=cat, callback_data=f"cat_{hotel}|{cat}") for cat in categories]]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="select_hotel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: безопасное удаление ===
async def safe_delete(message: types.Message):
    if message:
        try:
            await message.delete()
        except Exception as e:
            if "message to delete not found" not in str(e).lower():
                print(f"⚠ Ошибка при удалении сообщения: {e}")

# === ОБРАБОТЧИКИ ===

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    caption = (
        "🌟 *Добро пожаловать в сеть гостиниц!* 🌟\n\n"
        "• Нажмите **«📤 Отправить заявку»**, чтобы оставить заявку через Telegram\n"
        "• Или **«📅 Забронировать (Mini App)»** для удобного выбора в красивой форме"
    )
    try:
        photo = FSInputFile("iz_hotel1.jpg")
        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=get_main_inline_keyboard()
        )
    except FileNotFoundError:
        await message.answer(
            "📸 Фото временно недоступно, но гостиницы всё равно прекрасны!\n\n" + caption,
            parse_mode="Markdown",
            reply_markup=get_main_inline_keyboard()
        )

@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Вы вернулись в главное меню 🏠",
        reply_markup=get_main_inline_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "select_hotel")
async def select_hotel(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Выберите гостиницу:",
        reply_markup=get_hotel_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("hotel_"))
async def show_hotel_info(callback: types.CallbackQuery):
    hotel = callback.data.split("_", 1)[1]
    if hotel not in HOTELS:
        await callback.answer("Гостиница не найдена.", show_alert=True)
        return

    text = f"*🏨 Гостиница «{hotel}»*\n\n*Доступные категории:*\n\n"
    for cat, data in HOTELS[hotel].items():
        text += f"• *{cat}*\n  💰 {data['price']}\n  ℹ️ {data['info']}\n\n"

    await safe_delete(callback.message)
    await bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Отправить заявку", callback_data=f"book_hotel_{hotel}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="select_hotel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("book_hotel_"))
async def book_hotel_start(callback: types.CallbackQuery):
    hotel = callback.data.split("book_hotel_", 1)[1]
    if hotel not in HOTELS:
        await callback.answer("Гостиница не найдена.", show_alert=True)
        return

    await safe_delete(callback.message)
    await bot.send_message(
        chat_id=callback.from_user.id,
        text=f"🏨 Вы выбрали гостиницу *«{hotel}»*.\nВыберите категорию номера:",
        parse_mode="Markdown",
        reply_markup=get_category_keyboard(hotel)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def confirm_booking(callback: types.CallbackQuery):
    try:
        _, rest = callback.data.split("cat_", 1)
        hotel, category = rest.split("|", 1)
    except ValueError:
        await callback.answer("Ошибка выбора.", show_alert=True)
        return

    if hotel not in HOTELS or category not in HOTELS[hotel]:
        await callback.answer("Неверная категория или гостиница.", show_alert=True)
        return

    user_id = str(callback.from_user.id)
    user = callback.from_user
    existing = user_bookings.get(user_id)

    if existing:
        existing_hotel = existing.get("hotel", "Альфа")
        existing_cat = existing.get("category", "—")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, заменить", callback_data=f"confirm_replace_{hotel}|{category}")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="main_menu")]
        ])
        await safe_delete(callback.message)
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=(
                f"⚠ У вас уже есть бронирование:\n"
                f"• Гостиница: *{existing_hotel}*\n"
                f"• Категория: *{existing_cat}*\n\n"
                f"Хотите заменить его на *«{category}»* в *«{hotel}»*?"
            ),
            parse_mode="Markdown",
            reply_markup=kb
        )
        await callback.answer()
        return

    user_bookings[user_id] = {
        "hotel": hotel,
        "category": category,
        "username": user.username or "—",
        "full_name": user.full_name or "—",
        "status": "confirmed"
    }
    save_bookings(user_bookings)
    await _send_booking_confirmation(callback, hotel, category)
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_replace_"))
async def replace_booking(callback: types.CallbackQuery):
    try:
        _, rest = callback.data.split("confirm_replace_", 1)
        hotel, category = rest.split("|", 1)
    except ValueError:
        await callback.answer("Ошибка замены.", show_alert=True)
        return

    if hotel not in HOTELS or category not in HOTELS[hotel]:
        await callback.answer("Неверные данные.", show_alert=True)
        return

    user_id = str(callback.from_user.id)
    user = callback.from_user
    user_bookings[user_id] = {
        "hotel": hotel,
        "category": category,
        "username": user.username or "—",
        "full_name": user.full_name or "—",
        "status": "confirmed"
    }
    save_bookings(user_bookings)
    await _send_booking_confirmation(callback, hotel, category)
    await callback.answer()

async def _send_booking_confirmation(callback_or_message, hotel: str, category: str):
    await safe_delete(callback_or_message.message)

    text = (
        f"✅ Отлично! Вы отправили заявку на номер *«{category}»* в гостинице *«{hotel}»*.\n"
        f"Администратор скоро свяжется с вами."
    )

    user = callback_or_message.from_user
    await bot.send_message(
        chat_id=user.id,
        text=text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )

    if ADMIN_CHAT_ID:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"🛎 Новая заявка!\n"
                f"Гостиница: *{hotel}*\n"
                f"Категория: *{category}*\n"
                f"Пользователь: {user.full_name} (@{user.username or '—'})\n"
                f"ID: `{user.id}`"
            ),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "book_start")
async def book_start(callback: types.CallbackQuery):
    await select_hotel(callback)

@dp.callback_query(F.data == "show_my_booking")
async def show_my_booking(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    user_id = str(callback.from_user.id)
    if user_id in user_bookings:
        b = user_bookings[user_id]
        hotel = b.get("hotel", "Альфа")
        category = b.get("category", "—")
        full_name = b.get("full_name", "—")
        username = b.get("username", "—")

        text = (
            f"📌 Ваша заявка:\n\n"
            f"• Гостиница: *{hotel}*\n"
            f"• Категория: *{category}*\n"
            f"• Статус: ✅ Подтверждена\n"
            f"• Имя: {full_name}\n"
            f"• Username: @{username}\n\n"
            f"Хотите отменить?"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заявку", callback_data="cancel_confirm")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
        ])
    else:
        text = "📭 У вас пока нет заявок."
        kb = get_back_keyboard()

    await bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_confirm")
async def cancel_booking_confirm(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    user_id = str(callback.from_user.id)
    if user_id not in user_bookings:
        await callback.answer("Заявка уже отменена или не существует.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, отменить", callback_data="cancel_yes")],
        [InlineKeyboardButton(text="⬅️ Нет, оставить", callback_data="main_menu")]
    ])
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Вы уверены, что хотите отменить заявку?",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_yes")
async def do_cancel(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    user_id = str(callback.from_user.id)
    if user_id in user_bookings:
        booked = user_bookings.pop(user_id)
        save_bookings(user_bookings)
        hotel = booked.get("hotel", "Альфа")
        category = booked.get("category", "—")
        text = f"❌ Заявка на номер *«{category}»* в *«{hotel}»* отменена."
    else:
        text = "Заявка не найдена."

    await bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "send_admin_contact")
async def send_admin_contact(callback: types.CallbackQuery):
    await safe_delete(callback.message)
    await callback.message.answer_contact(
        phone_number=ADMIN_PHONE,
        first_name=ADMIN_NAME,
        vcard=f"BEGIN:VCARD\nVERSION:3.0\nFN:{ADMIN_NAME}\nTEL;TYPE=CELL:{ADMIN_PHONE}\nEND:VCARD"
    )
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="📞 Контакт отправлен.",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()

# === ОБРАБОТЧИК ДАННЫХ ИЗ MINI APP (ОПЦИОНАЛЬНО) ===
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)

        # Получаем гостиницу и категорию
        hotel = data.get("hotel")
        category = data.get("category")

        # Проверка обязательных полей
        if not hotel or not category:
            await message.answer(
                "❌ Не указаны гостиница или категория номера.",
                reply_markup=get_back_keyboard()
            )
            return

        # Проверка, что такая гостиница и категория существуют
        if hotel not in HOTELS or category not in HOTELS[hotel]:
            await message.answer(
                f"❌ Недопустимая комбинация:\n"
                f"Гостиница: *{hotel}*\n"
                f"Категория: *{category}*\n\n"
                f"Пожалуйста, выберите из предложенных вариантов.",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
            return

        # Формируем ФИО
        last_name = data.get("lastName", "").strip()
        first_name = data.get("firstName", "").strip()
        middle_name = data.get("middleName", "").strip()
        full_name = f"{last_name} {first_name}".strip()
        if middle_name:
            full_name += f" {middle_name}"
        full_name = full_name or "—"

        # Сохраняем полную бронь
        user_id = str(message.from_user.id)
        user_bookings[user_id] = {
            "hotel": hotel,
            "category": category,
            "status": "from_miniapp",
            "full_name": full_name,
            "username": message.from_user.username or "—",
            "phone": data.get("phone", "—"),
            "email": data.get("email") or "—",
            "guests": data.get("guests", 1),
            "passport_series": data.get("passportSeries", "—"),
            "passport_number": data.get("passportNumber", "—"),
            "issue_date": data.get("issueDate", "—"),
            "issued_by": data.get("issuedBy", "—"),
            "checkin": data.get("checkin", "—"),
            "checkout": data.get("checkout", "—"),
            "comment": data.get("comment") or "—"
        }
        save_bookings(user_bookings)

        # Ответ пользователю
        await message.answer(
            f"✅ Бронирование успешно отправлено!\n\n"
            f"🏨 *Гостиница:* {hotel}\n"
            f"🛏 *Категория:* {category}\n"
            f"👤 *Гость:* {full_name}\n"
            f"📅 *Даты:* {data.get('checkin')} – {data.get('checkout')}\n"
            f"📞 *Телефон:* {data.get('phone')}\n\n"
            f"Администратор свяжется с вами в ближайшее время.",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )

        # Уведомление администратору
        if ADMIN_CHAT_ID:
            admin_text = (
                f"🛎 **Новая бронь через Mini App!**\n\n"
                f"🏨 Гостиница: {hotel}\n"
                f"🛏 Категория: {category}\n"
                f"👤 Гость: {full_name}\n"
                f"📞 Телефон: {data.get('phone')}\n"
                f"📧 Email: {data.get('email', '—')}\n"
                f"👥 Гостей: {data.get('guests')}\n"
                f"📅 Даты: {data.get('checkin')} – {data.get('checkout')}\n"
                f"🛂 Паспорт: {data.get('passportSeries')} {data.get('passportNumber')}\n"
                f"Выдан: {data.get('issuedBy')} ({data.get('issueDate')})\n"
                f"💬 Комментарий: {data.get('comment', '—')}\n\n"
                f"ID: `{message.from_user.id}`\n"
                f"Username: @{message.from_user.username or '—'}"
            )
            await bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode="Markdown")

    except json.JSONDecodeError:
        await message.answer(
            "❌ Получены повреждённые данные. Попробуйте ещё раз.",
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка обработки Mini App: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке заявки. Пожалуйста, повторите попытку.",
            reply_markup=get_back_keyboard()
        )
# === ЗАПУСК ===
async def main():
    print("✅ Бот запущен!")
    if ADMIN_CHAT_ID:
        print(f"📨 Уведомления админу: включены (ID: {ADMIN_CHAT_ID})")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())