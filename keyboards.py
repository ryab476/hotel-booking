# === МОДУЛЬ КЛАВИАТУР === 

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from typing import List, Union, Dict, Any
from config import MINI_APP_URL

def reply_keyboard(
    buttons: List[List[Union[str, Dict[str, Any]]]], 
    resize: bool = True
) -> ReplyKeyboardMarkup:
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            if isinstance(button, dict):
                text = button["text"]
                if "web_app" in button:
                    web_app_info = WebAppInfo(url=button["web_app"])
                    btn = KeyboardButton(text=text, web_app=web_app_info)
                else:
                    btn = KeyboardButton(text=text)
            else:
                btn = KeyboardButton(text=button)
            keyboard_row.append(btn)
        keyboard.append(keyboard_row)
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=resize)

# === ИСПОЛЬЗОВАНИЕ ===
get_main_reply_keyboard = reply_keyboard([
    ['🏨 Выбрать гостиницу', '📤 Отправить заявку'],
    ['🎫 Мои брони', '📞 Связаться с админом'],
    [{'text': '📅 Забронировать', 'web_app': MINI_APP_URL}]
])
