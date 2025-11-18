# fastapi_app.py
import os
from fastapi import FastAPI, HTTPException
from config import BOT_TOKEN # Не используется в API, но пусть будет, если нужен
from database import init_db # <-- Импортируем init_db
from fastapi.middleware.cors import CORSMiddleware
import decimal # Импортируем decimal
from contextlib import asynccontextmanager # <-- Импортируем asynccontextmanager

# lifespan определяем ДО создания app
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск приложения (FastAPI API)...")
    try:
        # Инициализация БД при запуске приложения
        await init_db()
        print("✅ База данных инициализирована для FastAPI.")
        yield # <-- FastAPI начинает обслуживание
    except Exception as e:
        print(f"❌ Ошибка инициализации FastAPI приложения: {e}")
        raise e
    finally:
        print("🛑 Завершение работы приложения (FastAPI)...")

# Передаём lifespan в FastAPI
app = FastAPI(lifespan=lifespan)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # <-- Временно разрешено всё для отладки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API МАРШРУТЫ ===
@app.get("/api/hotels-with-categories")
async def get_hotels_with_categories_api():
    # Импортируем нужные функции из database.py
    from database import get_all_hotels, get_room_categories_by_hotel
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

        return result

    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка в /api/hotels-with-categories: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {str(e)}")

# Это блок только для ЛОКАЛЬНОГО запуска FastAPI
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Запуск FastAPI API сервера на порту {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)