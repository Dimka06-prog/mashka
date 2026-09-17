# -*- coding: utf-8 -*-
"""Formly — ИИ-тренер в Telegram. MVP для защиты."""
from __future__ import annotations

import http.client
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

API = "https://api.telegram.org/bot{token}/{method}"

EXERCISES = {
    "приседания": {
        "title": "Приседания",
        "setup": "Поставь телефон на стул, в кадр — весь корпус сбоку. Спина ровная, пятки на полу.",
        "cues": [
            "Голос: колени смотрят на носки, не заваливайся внутрь.",
            "Голос: таз ещё чуть ниже. Не отрывай пятки.",
            "Голос: корпус не кидай вперёд — грудь вверх.",
            "Голос: вставай через пятки, не через носки.",
        ],
        "photo": (
            "Разбор приседа по фото (MVP):\n"
            "• Колени — не должны сильно уходить внутрь\n"
            "• Спина — нейтральная, не круглая\n"
            "• Таз — опускается между стоп\n"
            "• Пятки — прижаты\n\n"
            "Оценка техники: 76/100 · риск коленей: средний\n"
            "Подсказка: отведи колени чуть в сторону носков и сядь на 5–8 см глубже."
        ),
    },
    "отжимания": {
        "title": "Отжимания",
        "setup": "Телефон сбоку. Тело — одна линия от пяток до макушки.",
        "cues": [
            "Голос: локти ближе к корпусу, не в стороны.",
            "Голос: таз не задирай — планка ровная.",
            "Голос: грудь к полу, шею не ломай.",
            "Голос: выдох на усилии, не проваливай поясницу.",
        ],
        "photo": (
            "Разбор отжимания по фото (MVP):\n"
            "• Тело — прямая линия\n"
            "• Локти — примерно 45° от корпуса\n"
            "• Голова — продолжение позвоночника\n\n"
            "Оценка техники: 71/100\n"
            "Подсказка: напряги живот, не поднимай таз выше плеч."
        ),
    },
    "планка": {
        "title": "Планка",
        "setup": "Камера сбоку. Локти под плечами, взгляд в пол чуть вперёд.",
        "cues": [
            "Голос: живот внутрь, не провисай.",
            "Голос: таз не домиком.",
            "Голос: пятки тяни назад, шея длинная.",
            "Голос: дыши ровно, держи ещё 10 секунд.",
        ],
        "photo": (
            "Разбор планки по фото (MVP):\n"
            "• Плечи над локтями\n"
            "• Таз не выше и не ниже линии тела\n"
            "• Поясница не провисает\n\n"
            "Оценка техники: 80/100\n"
            "Подсказка: подкрути таз на себя, как будто застегиваешь джинсы."
        ),
    },
    "выпады": {
        "title": "Выпады",
        "setup": "Камера сбоку на шаг. Переднее колено над стопой.",
        "cues": [
            "Голос: шаг шире, заднее колено к полу.",
            "Голос: переднее колено не заваливай внутрь.",
            "Голос: корпус прямой, не кланяйся в пол.",
            "Голос: оттолкнись передней пяткой вверх.",
        ],
        "photo": (
            "Разбор выпада по фото (MVP):\n"
            "• Переднее колено над стопой, не сильно вперёд за носок\n"
            "• Корпус вертикальный\n"
            "• Заднее колено смотрит в пол\n\n"
            "Оценка техники: 74/100\n"
            "Подсказка: сделай шаг длиннее и держи грудь вверх."
        ),
    },
}

MENU = {
    "keyboard": [
        [{"text": "Тренировка"}, {"text": "Разбор фото"}],
        [{"text": "Отчёт за неделю"}, {"text": "Тариф"}],
        [{"text": "Помощь"}],
    ],
    "resize_keyboard": True,
}
EX_KB = {
    "keyboard": [
        [{"text": "Приседания"}, {"text": "Отжимания"}],
        [{"text": "Планка"}, {"text": "Выпады"}],
        [{"text": "В меню"}],
    ],
    "resize_keyboard": True,
}
WORK_KB = {
    "keyboard": [
        [{"text": "Сделал повтор"}, {"text": "Закончить подход"}],
        [{"text": "В меню"}],
    ],
    "resize_keyboard": True,
}

USERS: dict[int, dict] = {}


def api(token: str, method: str, payload: dict | None = None, timeout: int = 60) -> dict:
    url = API.format(token=token, method=method)
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send(token: str, chat_id: int, text: str, keyboard: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    api(token, "sendMessage", payload, timeout=30)


def ex_key(text: str) -> str | None:
    t = (text or "").lower().strip()
    for k in EXERCISES:
        if k in t:
            return k
    return None


def handle(token: str, update: dict) -> None:
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return
    uid = msg.get("from", {}).get("id", chat_id)
    text = (msg.get("text") or "").strip()
    photo = msg.get("photo")
    st = USERS.setdefault(uid, {})
    low = text.lower()

    if text.startswith("/start") or low in {"в меню", "/menu", "меню"}:
        USERS[uid] = {}
        send(
            token,
            chat_id,
            "Formly — ИИ-тренер для домашних тренировок.\n\n"
            "Тренируйся дома. Техника — как с тренером.\n\n"
            "MVP: 4 упражнения, подсказки голосом и разбор фото.\n"
            "Поставь телефон на стул и выбери действие ниже.",
            MENU,
        )
        return
    if low in {"помощь", "/help"}:
        send(
            token,
            chat_id,
            "Как пользоваться:\n"
            "1) Тренировка — подсказки во время подхода\n"
            "2) Разбор фото — пришли кадр упражнения\n"
            "3) Отчёт — прогресс за неделю\n"
            "4) Тариф — 7 дней бесплатно, дальше 590 ₽/мес\n\n"
            "Это учебный MVP. Камера в боте имитирует разбор техники.",
            MENU,
        )
        return
    if "тариф" in low:
        send(
            token,
            chat_id,
            "Подписка Formly: 590 ₽ / мес\n"
            "7 дней бесплатно.\n\n"
            "Входит: разбор техники 4 упражнений и голосовые подсказки.\n"
            "Не входит: зал, питание, 200 упражнений.",
            MENU,
        )
        return
    if "отчёт" in low or "отчет" in low:
        send(
            token,
            chat_id,
            "Отчёт за неделю\n\n"
            "Тренировки: 3\n"
            "Средняя оценка техники: 78/100\n"
            "Лучше стало: глубина приседа\n"
            "Риск: колени иногда заваливаются внутрь\n\n"
            "Следующая цель: 3 тренировки без округления спины.",
            MENU,
        )
        return
    if "тренировка" in low:
        st["state"] = "pick_workout"
        send(token, chat_id, "Какое упражнение разбираем?", EX_KB)
        return
    if "разбор" in low or (low == "фото"):
        st["state"] = "pick_photo"
        send(token, chat_id, "Выбери упражнение, затем пришли фото сбоку.", EX_KB)
        return

    key = ex_key(text)
    if key and st.get("state") == "pick_workout":
        st.update(state="workout", exercise=key, reps=0)
        info = EXERCISES[key]
        send(
            token,
            chat_id,
            f"{info['title']}\n\n{info['setup']}\n\n"
            "Сделай повтор и нажми «Сделал повтор». Я дам подсказку, как голос тренера.",
            WORK_KB,
        )
        return
    if key and st.get("state") == "pick_photo":
        st.update(state="wait_photo", exercise=key)
        send(token, chat_id, f"Ок, ждём фото: {EXERCISES[key]['title']}. Снимай сбоку, в кадре весь корпус.")
        return

    if photo:
        key = st.get("exercise") or "приседания"
        st["state"] = None
        send(token, chat_id, EXERCISES[key]["photo"], MENU)
        return

    if st.get("state") == "workout" and ("сделал" in low or "повтор" in low):
        key = st.get("exercise", "приседания")
        reps = int(st.get("reps", 0)) + 1
        st["reps"] = reps
        cue = EXERCISES[key]["cues"][(reps - 1) % 4]
        send(token, chat_id, f"Повтор {reps}/8\n{cue}", WORK_KB)
        if reps >= 8:
            USERS[uid] = {}
            send(
                token,
                chat_id,
                "Подход закончен.\nОценка техники: 78/100 · риск коленей: средний.\n"
                "Не заваливай корпус вперёд на следующих 8 повторах.",
                MENU,
            )
        return
    if st.get("state") == "workout" and "закончить" in low:
        reps = st.get("reps", 0)
        USERS[uid] = {}
        send(
            token,
            chat_id,
            f"Подход закрыт. Повторов: {reps}.\nЧтобы техника росла — 3 таких подхода через день.",
            MENU,
        )
        return

    send(token, chat_id, "Нажми кнопку меню: тренировка, разбор фото, отчёт или тариф.", MENU)


def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token.startswith("вставь"):
        raise SystemExit("Нет токена в bot/.env")
    me = api(token, "getMe", timeout=30)["result"]
    print(f"Formly bot @{me.get('username')} запущен. Напиши /start", flush=True)
    offset = None
    while True:
        try:
            payload = {"timeout": 25, "drop_pending_updates": False}
            if offset is not None:
                payload["offset"] = offset
            data = api(token, "getUpdates", payload, timeout=40)
            for upd in data.get("result") or []:
                offset = upd["update_id"] + 1
                try:
                    handle(token, upd)
                except Exception as err:
                    print("handle error:", err, flush=True)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, http.client.RemoteDisconnected) as err:
            print("сеть, повтор через 3 сек:", err, flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
