from aiogram import F, Router
from aiogram.types import Message
from config import ADMIN_CONTACT, ADMIN_NAME

router = Router()
# 📞 Связаться с админом
@router.message(F.text == '📞 Связаться с админом')
async def contact_admin(message: Message):
    caption = (
        f"📞 *Контактная информация\n\n Администратор: {ADMIN_NAME}*\n\n"
        f"{ADMIN_CONTACT}\n\n"
        "Вы можете связаться напрямую или написать в Telegram."
    )
    await message.answer(caption, parse_mode="Markdown")