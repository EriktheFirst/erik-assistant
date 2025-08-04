import os
import logging
import asyncio

from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
import openai
from dotenv import load_dotenv

# Загрузка переменных окружения (если .env доступен)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("✅ TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("✅ OPENAI_API_KEY:", OPENAI_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask
app = Flask(__name__)

# Telegram
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# OpenAI
openai.api_key = OPENAI_API_KEY

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        logging.info(f"📨 Пользователь: {user_input}")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response['choices'][0]['message']['content'].strip()
        await update.message.reply_text(reply)
        logging.info("🤖 Ответ отправлен")

    except Exception as e:
        logging.error("❌ Ошибка GPT:", exc_info=e)
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook (асинхронный)
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        await application.process_update(update)
    except Exception as e:
        logging.error("❌ Ошибка во webhook:", exc_info=e)
        return "error", 400
    return "ok"

# Запуск Telegram + Flask
async def run():
    await application.initialize()
    await application.start()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run())
    app.run(host="0.0.0.0", port=10000)
