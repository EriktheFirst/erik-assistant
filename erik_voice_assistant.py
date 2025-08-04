import os
import logging
import asyncio
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import openai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN или OPENAI_API_KEY не установлены")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
openai.api_key = OPENAI_API_KEY

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logger.info("📩 Получено сообщение: %s", user_input)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        logger.error("❌ Ошибка от OpenAI: %s", e)
        reply = "Произошла ошибка при обращении к GPT."
    await update.message.reply_text(reply)

# Добавляем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask endpoint для webhook
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
        return "ok"
    except Exception as e:
        logger.error("❌ Ошибка во webhook: %s", e)
        return "error", 400

# Установка webhook
def set_webhook():
    url = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        data={"url": url}
    )
    logger.info("📡 Установка Webhook: %s", r.text)

# Запуск бота и сервера
async def run():
    await application.initialize()
    await application.start()
    set_webhook()
    logger.info("🚀 Telegram-бот и Webhook запущены")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run())
    app.run(host="0.0.0.0", port=10000)
