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
    raise SystemExit("Error: Telegram token not set. Створи .env з TG_TOKEN або встав токен у bot.py")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # наприклад: https://your-app.onrender.com
if not WEBHOOK_URL:
    raise SystemExit("Error: WEBHOOK_URL not set. Додай у Render змінну середовища")

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

# ---- Flask ----
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "ok", 200
    else:
        return "Bot is running", 200

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
        try:
            with open(VIDEO_FILE, "rb") as vid:
                #bot.send_video(chat_id, vid)
        except Exception as e:
            bot.send_message(chat_id, f"❗️ Не вдалося надіслати відео: {e}")
    else:
        bot.send_message(chat_id, "⚠️ Відео-привітання не знайдено.")

    bot.send_message(chat_id, WELCOME_TEXT, reply_markup=set_menu())

    links = DAILY_VIDEOS[0]
    for link in links:
        #bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
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
    first_run = True
    while True:
        if not first_run:
            time.sleep(86400)
        first_run = False

        for chat_id, day in list(user_progress.items()):
            if day < len(DAILY_VIDEOS):
                links = DAILY_VIDEOS[day]
                for link in links:
                    bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
                user_progress[chat_id] += 1

# ---- Запуск ----
if __name__ == "__main__":
    # Видаляємо старий webhook
    bot.remove_webhook()
    # Встановлюємо новий webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/")

    # Запускаємо потік для розсилки
    threading.Thread(target=daily_video_sender, daemon=True).start()

    # Flask-сервер (Render слухає 0.0.0.0:10000 або $PORT)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
