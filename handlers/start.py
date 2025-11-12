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
        "🌟 *Добро пожаловать в сеть гостиниц ГК \"ИЗМАЙЛОВО\"!* 🌟\n\n"
        "Здесь вы можете:\n"
        "• **«🏨 Выбрать гостиницу»**, чтобы посмотреть доступные категории номеров.\n"
        "• **«📤 Отправить заявку»**, чтобы оставить заявку через Telegram.\n"
        "• Посмотреть ранее отправленные заявки **«🎫 Мои брони»**.\n"
        "• **«📞 Связаться с админом»**, чтобы получить контактную информацию.\n"
        "• Ввести полные данные для бронирования в мини приложении **«📅 Забронировать номер»**"
    )
    try:
        photo = FSInputFile("images\iz_hotel1.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")
    except FileNotFoundError:
        await message.answer("📸 Фото временно недоступно, но гостиницы всё равно прекрасны!\n\n" + caption, parse_mode="Markdown")

    await message.answer("Выберите действие:", reply_markup=get_main_reply_keyboard)

# Возвращаем роутер
def setup_router():
    return router