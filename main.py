import asyncio
import logging
import os
import decimal # Импортируем decimal
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from config import BOT_TOKEN # Убедись, что это НЕ запускает polling или webhook напрямую
from database import init_db, get_all_hotels, get_room_categories_by_hotel

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
bot = None
dp = None

# === ИМПОРТИРУЕМ РОУТЕРЫ НА УРОВНЕ МОДУЛЯ ===
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

# === УПРОЩЁННЫЙ ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ (lifespan) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp
    print("🚀 Запуск приложения...")

    try:
        # Инициализация БД
        await init_db()
        print("✅ База данных инициализирована.")

        # Создание бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        print("✅ Bot и Dispatcher созданы.")

        # Подключаем роутеры
        dp.include_router(start_router)
        dp.include_router(booking_router)
        dp.include_router(hotels_router)
        dp.include_router(bookings_router)
        dp.include_router(admin_router)
        dp.include_router(webapp_router)
        dp.include_router(error_router) # Подключаем роутер с обработчиком ошибок
        print("✅ Роутеры подключены.")

        # Устанавливаем вебхук
        webhook_url = f"https://hotel-booking-xxb7.onrender.com/webhook"
        await bot.set_webhook(webhook_url)
        print(f"✅ Webhook установлен на {webhook_url}")

        print("✅ aiogram Dispatcher и Bot инициализированы, webhook установлен.")
        yield  # <-- FastAPI начинает обслуживание запросов здесь.

    except Exception as e:
        # Логируем любую ошибку, которая происходит ВНУТРИ lifespan
        logging.error(f"Ошибка в lifespan: {e}")
        # Не вызываем raise, чтобы не уронить процесс раньше времени, если возможно.
        # Но в данном случае, если set_webhook не проходит, приложение бесполезно.
        raise e # Лучше упасть с ясной ошибкой

    finally:
        # Очистка
        if bot:
            await bot.delete_webhook()
            await bot.session.close()
        print("🛑 Завершение работы бота...")

app = FastAPI(lifespan=lifespan)

# === CORS ===
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://t.me", "https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API МАРШРУТЫ ===
@app.get("/api/hotels-with-categories")
async def get_hotels_with_categories_api():
    try:
        hotels = await get_all_hotels(sort_by="name", desc=False)
        result = []
        for hotel in hotels:
            categories = await get_room_categories_by_hotel(hotel["id"])
            hotel_data = {
                "id": hotel["id"],
                "name": hotel["name"],
                "categories": [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        # Преобразуем Decimal в int или float перед включением в JSON
                        "price": float(c["price"]) if isinstance(c["price"], (decimal.Decimal, float)) else c["price"]
                    }
                    for c in categories
                ]
            }
            result.append(hotel_data)

        # Создаем ответ с CORS-заголовками
        return JSONResponse(
            content=result,
            headers={
                "Access-Control-Allow-Origin": "https://t.me",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as e:
        # Логируем ошибку
        logging.error(f"Ошибка в /api/hotels-with-categories: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {str(e)}")

# === Webhook ===
@app.post("/webhook")
async def webhook_handler(update: dict):
    global dp, bot
    if dp is None or bot is None:
        logging.error("Dispatcher или Bot не инициализированы при получении вебхука!")
        return {"status": "error", "reason": "Not initialized"}
    from aiogram.types import Update
    update_obj = Update(**update)
    await dp.feed_raw_update(bot, update_obj)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Running!"}

# Это блок только для ЛОКАЛЬНОГО запуска
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)