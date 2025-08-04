import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import openai
from dotenv import load_dotenv

# Загрузка переменных среды
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Создание Telegram-приложения
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# OpenAI API
openai.api_key = OPENAI_API_KEY

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Ошибка при обращении к OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса.")

# Регистрируем handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Инициализируем Telegram Application
@app.before_first_request
def init_telegram_app():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

# Webhook endpoint
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        logging.error("❌ Ошибка во webhook:", exc_info=e)
        return "error", 400

# Запуск Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
