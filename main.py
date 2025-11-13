import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os
from config import BOT_TOKEN  # Убедись, что BOT_TOKEN определён в config
from database import init_db

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# URL вебхука для Render
WEBHOOK_URL = "https://hotel-booking-xxb7.onrender.com"
WEBHOOK_PATH = "/webhook"  # Путь, по которому Render будет принимать обновления от Telegram

# Порт, который использует Render
PORT = int(os.getenv("PORT", 10000))

# Хост, на котором будет работать сервер (Render требует 0.0.0.0)
HOST = "0.0.0.0"

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
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # === РЕГИСТРАЦИЯ РОУТЕРОВ ===
    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(hotels_router)
    dp.include_router(bookings_router)
    dp.include_router(admin_router)
    dp.include_router(webapp_router)

    # Устанавливаем webhook
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")

    # Настраиваем aiohttp приложение
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    print(f"✅ Webhook установлен на {WEBHOOK_URL}{WEBHOOK_PATH}")
    print(f"Сервер запущен на {HOST}:{PORT}")

    # Ожидаем завершения
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.delete_webhook()  # Удаляем webhook при завершении

if __name__ == "__main__":
    asyncio.run(main())