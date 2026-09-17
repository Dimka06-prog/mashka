#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  echo "Создайте файл .env и вставьте токен от @BotFather"
  touch .env
  echo "BOT_TOKEN=ваш_токен_от_BotFather" > .env
  open -e .env
  echo "Откройте .env и вставьте токен, затем запустите скрипт снова"
  exit 1
fi
source .venv/bin/activate
pip install -r requirements.txt -q
python3 bot.py
