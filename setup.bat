@echo off
echo ================================
echo   Store Tracker - Kurulum
echo ================================
echo.
echo Bagimliliklar yukleniyor...
pip install -r requirements.txt
echo.
echo Baslatiliyor: http://localhost:8000
echo.
python main.py
