# import asyncio # Закомментировано, так как не используется
import logging
import os
#import decimal 
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN 
from database import init_db
# Простой middleware для логирования обновлений (опционально)
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any
import logging

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === ИМПОРТИРУЕМ РОУТЕРЫ НА УРОВНЕ МОДУЛЯ (но пока не подключаем) ===
from handlers.start import router as start_router
from handlers.booking import router as booking_router
from handlers.hotels import router as hotels_router
from handlers.bookings import router as bookings_router
from handlers.admin import router as admin_router
from handlers.webapp import router as webapp_router

# === ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК AIORAM ===
from aiogram import Router
from aiogram.types import ErrorEvent

error_router = Router()

@error_router.errors()
async def error_handler(event: ErrorEvent):
    logging.error(f"Произошла ошибка внутри обработчика aiogram: {event.exception}")

async def main():
    # Проверяем переменную окружения PROD, по умолчанию считаем, что режим - development (polling)
    prod_mode = os.getenv("PROD", "false").lower() == "true"
    print(f"🔄 Режим запуска: {'Production (webhook)' if prod_mode else 'Development (polling)'}")

    if prod_mode:
        print("❌ Этот режим (PROD) не реализован в этом упрощенном скрипте.")
        print("   Для PROD используйте запуск через uvicorn напрямую с установленным PROD=true.")
        return

    print("🚀 Запуск приложения (Development - только бот)...")

    # Инициализация БД
    await init_db()
    print("✅ База данных инициализирована.")

    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    print("✅ Bot и Dispatcher созданы.")

    # Удаляем webhook, чтобы избежать конфликта при polling
    await bot.delete_webhook(drop_pending_updates=True) # drop_pending_updates=True очищает очередь обновлений, пришедших на webhook
    print("🧹 Webhook удален, готов к polling.")

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(hotels_router)
    dp.include_router(bookings_router)
    dp.include_router(admin_router)
    dp.include_router(webapp_router)
    dp.include_router(error_router) # Подключаем роутер с обработчиком ошибок
    print("✅ Роутеры подключены.")

    class LogUpdatesMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable,
            event: object,
            data: Dict[str, Any]  
        ) -> Any:
                # Пытаемся определить тип события и user_id более явно
                event_type = type(event).__name__ # Получаем имя класса события
                user_id = "unknown_user"
                if hasattr(event, 'from_user') and event.from_user:
                    user_id = event.from_user.id
                elif hasattr(event, 'message') and event.message and event.message.from_user:
                     user_id = event.message.from_user.id
                elif hasattr(event, 'callback_query') and event.callback_query and event.callback_query.from_user:
                     user_id = event.callback_query.from_user.id
                # Можно добавить другие типы, если нужно
                
                #logging.info(f"Получено обновление (Middleware): {event_type}, от user_id: {user_id}, сам event: {event}")
                return await handler(event, data)

    # Добавляем middleware к диспетчеру
    dp.update.middleware(LogUpdatesMiddleware())

    # Добавим лог в main.py после инициализации
    from database import db_pool
    if db_pool is None:
        logging.error("main.py: db_pool всё ещё None после init_db!")
    else:
        logging.info(f"main.py: db_pool инициализирован, тип: {type(db_pool)}")

    print("🤖 Запуск aiogram polling...")
    # Запускаем polling. Это блокирующая операция.
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())