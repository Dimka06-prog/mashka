@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env >nul
  echo Открой файл .env и вставь токен от @BotFather
  notepad .env
  pause
)
py -3 -m pip install -r requirements.txt -q
py -3 bot.py
pause
