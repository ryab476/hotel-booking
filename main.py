
# === ГЛАВНЫЙ МОДУЛЬ === 
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db

async def main():
    await init_db()  # ← Сначала инициализируем БД
    
    # === ИМПОРТ РОУТЕРОВ (теперь db_pool доступен) ===
    from handlers.start import router as start_router
    from handlers.booking import router as booking_router
    from handlers.hotels import router as hotels_router
    from handlers.bookings import router as bookings_router
    from handlers.admin import router as admin_router
    from handlers.webapp import router as webapp_router

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # === РЕГИСТРАЦИЯ РОУТЕРОВ ===
    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(hotels_router)
    dp.include_router(bookings_router)
    dp.include_router(admin_router)
    dp.include_router(webapp_router)

    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())