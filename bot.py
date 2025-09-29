# bot.py
"""
Бот для Render:
- При /start надсилає відео (повноцінне) + текст + перше відео з YouTube.
- У меню є кнопка "Старт" і "Чат".
- Протягом наступних 4 днів надсилає YouTube-відео.
Працює через webhook + Flask.
"""

import os
import time
import logging
import threading
from dotenv import load_dotenv
import telebot
from telebot import types
from flask import Flask, request

# ---- Конфігурація ----
load_dotenv()
TOKEN = os.getenv("TG_TOKEN")
if not TOKEN:
    raise SystemExit("Error: Telegram token not set")

APP_URL = os.getenv("APP_URL")  # наприклад: https://mybot.onrender.com

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
mp4_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".mp4")]
VIDEO_FILE = os.path.join(BASE_DIR, mp4_files[0]) if mp4_files else None

WELCOME_TEXT = (
    "Вітаю! 👋\n\n"
    "Дякуємо, що приєдналися. "
    "Якщо виникнуть запитання — просто відповідай у цьому чаті."
)

DAILY_VIDEOS = [
    ["https://youtu.be/rk_OnILnnKo"],
    ["https://youtu.be/uRYaPJKQAtQ"],
    ["https://youtu.be/AK94MMGKyW4", "https://youtu.be/i2oURWmChBs"],
    ["https://youtu.be/_e_zuad1zYQ"],
    ["https://youtu.be/t41VgcVAim4"],
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
user_progress = {}

# ---- Меню ----
def set_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton("🚀 Старт")
    btn_chat = types.KeyboardButton("💬 Чат")
    menu.add(btn_start, btn_chat)
    return menu

# ---- Обробники ----
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    user_progress[chat_id] = 0

    if VIDEO_FILE and os.path.exists(VIDEO_FILE):
        with open(VIDEO_FILE, "rb") as vid:
            bot.send_video(chat_id, vid)
    else:
        bot.send_message(chat_id, "⚠️ Відео-привітання не знайдено.")

    time.sleep(0.5)
    bot.send_message(chat_id, WELCOME_TEXT, reply_markup=set_menu())

    time.sleep(0.5)
    for link in DAILY_VIDEOS[0]:
        bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
    user_progress[chat_id] = 1

@bot.message_handler(func=lambda msg: msg.text == "🚀 Старт")
def btn_start_handler(message):
    cmd_start(message)

@bot.message_handler(func=lambda msg: msg.text == "💬 Чат")
def btn_chat_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Приєднуйся до нашої групи: https://t.me/+OK2iQEehXZViYWMy")

# ---- Автоматична розсилка ----
def daily_video_sender():
    while True:
        time.sleep(24 * 60 * 60)  # раз на добу
        for chat_id, day in list(user_progress.items()):
            if day < len(DAILY_VIDEOS):
                for link in DAILY_VIDEOS[day]:
                    bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
                user_progress[chat_id] += 1

# ---- Flask додаток ----
app = Flask(__name__)

@app.route("/webhook", methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running", 200

# ---- Запуск ----
if __name__ == "__main__":
    # Ставимо webhook
    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/webhook")

    # запускаємо окремий потік для розсилки
    threading.Thread(target=daily_video_sender, daemon=True).start()

    # Запускаємо Flask-сервер (порт 10000 для Render)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
