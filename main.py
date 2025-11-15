import asyncio
import logging
import os
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, HTTPException
from config import BOT_TOKEN
from database import init_db, get_all_hotels, get_room_categories_by_hotel

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
bot = None
dp = None

# === ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ (lifespan) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp

    print("🚀 Запуск приложения...")
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # === Подключаем роутеры aiogram ===
    from handlers.start import router as start_router
    from handlers.booking import router as booking_router
    from handlers.hotels import router as hotels_router
    from handlers.bookings import router as bookings_router
    from handlers.admin import router as admin_router
    from handlers.webapp import router as webapp_router  # ← Убедитесь, что он подключен

    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(hotels_router)
    dp.include_router(bookings_router)
    dp.include_router(admin_router)
    dp.include_router(webapp_router)

    # Устанавливаем webhook для бота (Render -> Telegram)
    webhook_url = f"https://hotel-booking-xxb7.onrender.com/webhook"
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook установлен на {webhook_url}")

    yield  # Работа приложения (FastAPI + aiogram)

    # Завершение работы
    await bot.delete_webhook()
    await bot.session.close()
    print("🛑 Завершение работы бота...")

# === FASTAPI ПРИЛОЖЕНИЕ ===
app = FastAPI(lifespan=lifespan)

# === CORS для MiniApp ===
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://t.me"],  # ← Разрешаем MiniApp
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API МАРШРУТЫ ===

# --- Существующие маршруты ---
@app.get("/api/hotels")
async def get_hotels_api():
    hotels = await get_all_hotels(sort_by="name", desc=False)
    return [{"id": h["id"], "name": h["name"]} for h in hotels]

@app.get("/api/hotels/{hotel_id}/categories")
async def get_categories_api(hotel_id: int):
    categories = await get_room_categories_by_hotel(hotel_id)
    return [{"id": c["id"], "name": c["name"], "price": c["price"]} for c in categories]

# --- НОВЫЙ МАРШРУТ: /api/hotels-with-categories ---
@app.get("/api/hotels-with-categories")
async def get_hotels_with_categories_api():
    try:
        # Получаем все гостиницы
        hotels = await get_all_hotels(sort_by="name", desc=False)

        # Для каждой гостиницы получаем её категории
        result = []
        for hotel in hotels:
            categories = await get_room_categories_by_hotel(hotel["id"])
            # Формируем объект с гостиницей и её категориями
            hotel_data = {
                "id": hotel["id"],
                "name": hotel["name"],
                "categories": [
                    {"id": c["id"], "name": c["name"], "price": c["price"]}
                    for c in categories
                ]
            }
            result.append(hotel_data)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {str(e)}")

# === МАРШРУТ ДЛЯ WEBHOOK (Telegram -> Render -> Bot) ===
@app.post("/webhook")
async def webhook_handler(update: dict):
    # Передаём обновление aiogram
    from aiogram.types import Update
    update_obj = Update(**update)
    await dp.feed_raw_update(bot, update_obj)
    return {"status": "ok"}

# === ТЕСТОВЫЙ МАРШРУТ ===
@app.get("/")
async def root():
    return {"message": "FastAPI + aiogram bot is running on Render!"}

# === ЗАПУСК (только для локального тестирования) ===
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))  # ← Render использует PORT
    uvicorn.run(app, host="0.0.0.0", port=port)