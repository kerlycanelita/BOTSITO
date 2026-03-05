@echo off
echo Reiniciando bot...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
timeout /t 2 >nul
python main.py
pause
