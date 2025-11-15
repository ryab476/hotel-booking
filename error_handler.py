import logging
from aiogram import Router
from aiogram.types import ErrorEvent # Импортируем ErrorEvent
from aiogram.handlers import ErrorHandler # Импортируем базовый ErrorHandler

router = Router()

# Создаём асинхронную функцию для обработки ошибок
@router.errors() # Используем декоратор для перехвата ошибок
async def error_handler(event: ErrorEvent):
    """
    Глобальный обработчик ошибок aiogram.
    """
    logging.error(f"Произошла ошибка внутри обработчика aiogram: {event.exception}")
    # Ты можешь добавить дополнительную логику здесь, например, отправку уведомлений администратору.
    # ВАЖНО: Не вызывай здесь API Telegram, если ошибка связана с сетью, чтобы не вызвать рекурсию.
    # Просто логги и возвращайся.

# Опционально: Наследуйся от ErrorHandler для более сложной логики
# class MyErrorHandler(ErrorHandler):
#     async def handle(self, request, exception):
#         logging.error(f"ErrorHandler: {exception}")
#         # Сделать что-то ещё
#         return await super().handle(request, exception)

# my_error_handler = MyErrorHandler()
