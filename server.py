from flask import Flask, request
import telebot
import time

TOKEN = "8424933564:AAHKNuz4K5dSa5qukhAjL2yuChYpO1CZyrc"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Тут будемо зберігати користувачів і час закінчення доступу
users_access = {}

@app.route("/wayforpay", methods=['POST'])
def wayforpay_callback():
    data = request.json
    telegram_id = int(data.get("telegram_id"))  # сайт повинен передати ID
    users_access[telegram_id] = time.time() + 60*60*24*60  # 2 місяці
    bot.send_message(telegram_id, "✅ Оплата підтверджена! Доступ відкрито на 2 місяці.")
    return "OK"

if __name__ == "__main__":
    app.run(port=5000)
