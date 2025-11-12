# === МОДУЛЬ ВЗАИМОДЕЙСТВИЯ С БД === 

import asyncpg
from config import DATABASE_URL
from datetime import date
from typing import List, Dict, Any

db_pool = None

async def init_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ Успешное подключение к PostgreSQL")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise

    async with db_pool.acquire() as conn:
        # Создание таблиц
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                address TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS room_categories (
                id SERIAL PRIMARY KEY,
                hotel_id INTEGER REFERENCES hotels(id),
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                hotel_id INTEGER REFERENCES hotels(id),
                room_category_id INTEGER REFERENCES room_categories(id),
                check_in DATE,
                check_out DATE,
                status TEXT DEFAULT 'Заявка',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Заполнение начальных данных
        hotels_count = await conn.fetchval("SELECT COUNT(*) FROM hotels")
        if hotels_count == 0:
            await conn.execute("INSERT INTO hotels (name, description) VALUES ($1, $2)", "Альфа", "Описание гостиницы Альфа")
            await conn.execute("INSERT INTO hotels (name, description) VALUES ($1, $2)", "Бетта", "Описание гостиницы Бетта")
            await conn.execute("INSERT INTO hotels (name, description) VALUES ($1, $2)", "Гамма-Дельта", "Описание гостиницы Гамма-Дельта")

# === ФУНКЦИИ РАБОТЫ С БАЗОЙ ===
async def get_all_hotels(sort_by: str = "name", desc: bool = False):
    order = "DESC" if desc else "ASC"
    valid_sort_fields = {
        "name": "name",
        "created": "created_at"
    }
    order_field = valid_sort_fields.get(sort_by, "name")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, name, description, address FROM hotels ORDER BY {order_field} {order}"
        )
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "address": r["address"]
            }
            for r in rows
        ]

async def get_hotel_by_id(hotel_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, description FROM hotels WHERE id = $1", hotel_id)
        return {"id": row["id"], "name": row["name"], "description": row["description"]} if row else None

async def get_room_categories_by_hotel(hotel_id: int):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, price FROM room_categories WHERE hotel_id = $1", hotel_id)
        return [{"id": r["id"], "name": r["name"], "description": r["description"], "price": r["price"]} for r in rows]

async def get_room_category_by_id(category_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, description, price FROM room_categories WHERE id = $1", category_id)
        return {"id": row["id"], "name": row["name"], "description": row["description"], "price": row["price"]} if row else None

async def get_user_bookings(telegram_id: int):
    """Получить активные (неотменённые) бронирования пользователя"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT b.id, h.name as hotel_name, rc.name as room_category, 
                   b.check_in, b.check_out, b.status
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.id
            JOIN room_categories rc ON b.room_category_id = rc.id
            WHERE b.telegram_id = $1 AND b.status != 'cancelled'
            ORDER BY b.created_at DESC
        """, telegram_id)
        return [{
            "id": r["id"], 
            "hotel_name": r["hotel_name"], 
            "room_category": r["room_category"],
            "check_in": r["check_in"],
            "check_out": r["check_out"],
            "status": r["status"]
        } for r in rows]

async def create_booking(telegram_id: int, hotel_id: int, room_category_id: int, check_in: str, check_out: str):
    check_in_date = date.fromisoformat(check_in)
    check_out_date = date.fromisoformat(check_out)
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bookings (telegram_id, hotel_id, room_category_id, check_in, check_out)
            VALUES ($1, $2, $3, $4, $5)
        """, telegram_id, hotel_id, room_category_id, check_in_date, check_out_date)

async def has_overlapping_booking(telegram_id: int, new_check_in: str, new_check_out: str):
    """Проверяет, есть ли у пользователя бронирования, пересекающиеся с новыми датами"""
    new_check_in_date = date.fromisoformat(new_check_in)
    new_check_out_date = date.fromisoformat(new_check_out)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT check_in, check_out FROM bookings WHERE telegram_id = $1 AND status != 'cancelled'",
            telegram_id
        )
        
        for row in rows:
            existing_check_in = row["check_in"]
            existing_check_out = row["check_out"]
            
            # Проверяем пересечение:
            # Новый заезд < выезда_существующего И выезд_новый > заезда_существующего
            if new_check_in_date < existing_check_out and new_check_out_date > existing_check_in:
                return True  # Найдено пересечение
    return False 

async def get_user_booking_by_id(booking_id: int, telegram_id: int):
    """Получить конкретное бронирование пользователя по ID"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT b.id, h.name as hotel_name, rc.name as room_category, 
                   b.check_in, b.check_out, b.status
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.id
            JOIN room_categories rc ON b.room_category_id = rc.id
            WHERE b.id = $1 AND b.telegram_id = $2
        """, booking_id, telegram_id)
        
        return dict(row) if row else None

async def update_booking_status(booking_id: int, status: str):
    """Обновить статус бронирования"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE bookings SET status = $1 WHERE id = $2",
            status, booking_id
        )   

async def has_overlapping_booking(telegram_id: int, new_check_in: str, new_check_out: str):
    """Проверяет, есть ли у пользователя бронирования, пересекающиеся с новыми датами"""
    new_check_in_date = date.fromisoformat(new_check_in)
    new_check_out_date = date.fromisoformat(new_check_out)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT check_in, check_out FROM bookings WHERE telegram_id = $1 AND status != 'cancelled'",
            telegram_id
        )
        
        for row in rows:
            existing_check_in = row["check_in"]
            existing_check_out = row["check_out"]
            
            # Пересечение: новый заезд < выезда_существующего И выезд_новый > заезда_существующего
            if new_check_in_date < existing_check_out and new_check_out_date > existing_check_in:
                return True  # Найдено пересечение
    return False            