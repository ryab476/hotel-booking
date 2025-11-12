
# === МОДУЛЬ MINIAPP === 
from aiogram import F, Router
from aiogram.types import Message
from keyboards import get_main_reply_keyboard
from utils import sanitize_miniapp_data_universal
import json
import logging
from database import has_overlapping_booking, create_booking, get_hotel_by_id, get_room_category_by_id
from datetime import date


router = Router()

@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        web_app_data = message.web_app_data.data
        logging.info(f"🟩 RAW DATA from MiniApp: {web_app_data}")
        
        data = json.loads(web_app_data)
        validated_data = sanitize_miniapp_data_universal(data)
        
        hotel_id = validated_data.get("hotel_id")
        room_category_id = validated_data.get("room_category_id")
        check_in = validated_data.get("check_in")
        check_out = validated_data.get("check_out")
        
        logging.info(f"🟩 EXTRACTED: hotel_id={hotel_id}, room_cat={room_category_id}, in={check_in}, out={check_out}")
        
        if not all([hotel_id, room_category_id, check_in, check_out]):
            missing = []
            if not hotel_id: missing.append("hotel_id")
            if not room_category_id: missing.append("room_category_id")
            if not check_in: missing.append("check_in")
            if not check_out: missing.append("check_out")
            
            await message.answer(
                f"❌ Не все данные заполнены. Отсутствуют: {missing}\n"
                "Пожалуйста, проверьте форму.",
                parse_mode="Markdown"
            )
            return
        
        # 🔍 Проверка пересечения дат
        user_id = message.from_user.id
        if await has_overlapping_booking(user_id, check_in, check_out):
            await message.answer(
                "❌ У вас уже есть бронирование на эти даты!\n"
                "Невозможно создать новое бронирование с пересекающимися датами.",
                parse_mode="Markdown"
            )
            return
        
        # ✅ Создаем бронь
        await create_booking(
            telegram_id=user_id,
            hotel_id=int(hotel_id),
            room_category_id=int(room_category_id),
            check_in=check_in,
            check_out=check_out
        )
        
        hotel_info = await get_hotel_by_id(int(hotel_id))
        room_info = await get_room_category_by_id(int(room_category_id))
        
        caption = (
            f"✅ *Бронирование успешно создано!*\n\n"
            f"🏨 {hotel_info['name']}\n"
            f"🛏️ {room_info['name']}\n"
            f"📅 {check_in} — {check_out}\n\n"
            f"Спасибо за заявку!"
        )
        await message.answer(caption, parse_mode="Markdown", reply_markup=get_main_reply_keyboard)
        
    except json.JSONDecodeError:
        await message.answer("❌ Ошибка разбора данных из формы.")
    except ValueError as e:
        await message.answer(f"❌ Ошибка в данных: {e}")
    except Exception as e:
        logging.error(f"Ошибка обработки WebApp данных: {e}")
        await message.answer("❌ Произошла ошибка при сохранении заявки.")