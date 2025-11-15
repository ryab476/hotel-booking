# === СТАРТОВЫЙ МОДУЛЬ === 

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import get_main_reply_keyboard
from aiogram import Bot
from config import BOT_TOKEN
from aiogram.types import FSInputFile

router = Router()
bot = Bot(token=BOT_TOKEN)

@router.message(CommandStart())
async def cmd_start(message: Message):
    caption = (
        "🌟 Добро пожаловать в ГК «Измайлово»!\n\n"
        "Выберите действие:\n"
        "• 🏨 Выбрать гостиницу — посмотрите доступные номера\n"
        "• 📅 Забронировать — заполните данные в мини-приложении\n"
        "• 📤 Отправить заявку — отправьте запрос администратору\n"
        "• 🎫 Мои брони — просмотрите историю заявок\n"
        "• 📞 Связаться с админом — получите контакты"
    )
    # try:
    #      photo = FSInputFile("images\iz_hotel1.jpg")
    #      await message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")
    # except FileNotFoundError:
    #      await message.answer("📸 Фото временно недоступно, но гостиницы всё равно прекрасны!\n\n" + caption, parse_mode="Markdown")

    await message.answer("Выберите действие:", reply_markup=get_main_reply_keyboard)

# Возвращаем роутер
def setup_router():
    return router