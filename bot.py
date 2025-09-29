"""
Простий та надійний бот:
- При /start надсилає відео (повноцінне, не кружечок) + текст + перше відео з YouTube.
- У меню є кнопка "Старт" та кнопка "Чат", яка веде в групу.
- Кожному користувачу протягом наступних 4 днів автоматично надсилає відео з YouTube.
"""

import os
import time
import logging
import threading
from dotenv import load_dotenv
import telebot
from telebot import types

# ---- Конфігурація ----
load_dotenv()
TOKEN = os.getenv("TG_TOKEN")
if not TOKEN:
    raise SystemExit("Error: Telegram token not set. Створи .env з TG_TOKEN або встав токен у bot.py")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Шукаємо перший mp4 у папці
mp4_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".mp4")]
VIDEO_FILE = os.path.join(BASE_DIR, mp4_files[0]) if mp4_files else None

WELCOME_TEXT = (
    "Вітаю! 👋\n\n"
    "Дякуємо, що приєдналися. "
    "Якщо виникнуть запитання — просто відповідай у цьому чаті."
)

# Лінки на YouTube (на 5 днів)
DAILY_VIDEOS = [
    ["https://youtu.be/rk_OnILnnKo"],
    ["https://youtu.be/uRYaPJKQAtQ"],
    ["https://youtu.be/AK94MMGKyW4", "https://youtu.be/i2oURWmChBs"],
    ["https://youtu.be/_e_zuad1zYQ"],
    ["https://youtu.be/t41VgcVAim4"],
]

# ---- Логування ----
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---- Ініціалізація бота ----
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Пам’ятаємо користувачів та день
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
    user_progress[chat_id] = 0  # починаємо з першого дня

    log.info(f"/start from {message.from_user.id} @{message.from_user.username}")

    # Надсилаємо привітальне відео
    if VIDEO_FILE and os.path.exists(VIDEO_FILE):
        try:
            with open(VIDEO_FILE, "rb") as vid:
                bot.send_video(chat_id, vid)
        except Exception as e:
            log.exception("Cannot send video")
            bot.send_message(chat_id, f"❗️ Не вдалося надіслати відео: {e}")
    else:
        bot.send_message(chat_id, "⚠️ Відео-привітання не знайдено.")

    time.sleep(0.5)
    # Надсилаємо привітальний текст
    bot.send_message(chat_id, WELCOME_TEXT, reply_markup=set_menu())

    time.sleep(0.5)
    # Надсилаємо перше відео з YouTube
    links = DAILY_VIDEOS[0]
    for link in links:
        bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
    user_progress[chat_id] = 1  # Переходимо до другого дня

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
            time.sleep(86400)  # чекаємо лише з другого кола
        first_run = False

        for chat_id, day in list(user_progress.items()):
            if day < len(DAILY_VIDEOS):
                links = DAILY_VIDEOS[day]
                for link in links:
                    bot.send_message(chat_id, f"🎬 Ваше відео на сьогодні: {link}")
                user_progress[chat_id] += 1

# ---- Запуск ----
if __name__ == "__main__":
    print("Bot is running. Press Ctrl+C to stop.")
    try:
        # спочатку видаляємо webhook, щоб уникнути Conflict 409
        bot.remove_webhook()

        # запускаємо окремий потік для розсилки
        threading.Thread(target=daily_video_sender, daemon=True).start()

        # а тепер polling
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        log.exception("Bot polling crashed")