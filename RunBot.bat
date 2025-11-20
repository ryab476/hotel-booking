@echo off
chcp 65001 >nul
REM Запуск fastapi_app.py в новом окне cmd
start "FastAPI App" /min cmd /c "D:\Pyton\Booking\.conda\python.exe e:/MyProjects/hotel-booking2/fastapi_app.py"

REM Запуск main.py в новом окне cmd
start "Main Bot" /min cmd /c "D:\Pyton\Booking\.conda\python.exe e:/MyProjects/hotel-booking2/main.py"

echo Оба скрипта запущены в отдельных окнах.