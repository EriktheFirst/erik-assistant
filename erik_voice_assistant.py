import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import asyncio
import requests

# === Загрузка токенов ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("✅ TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("✅ OPENAI_API_KEY:", OPENAI_API_KEY)

# === Flask app ===
app = Flask(__name__)

# === Telegram bot и app ===
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === OpenAI ===
openai.api_key = OPENAI_API_KEY

# === Логирование ===
logging.basicConfig(level=logging.INFO)

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# === Обработка сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        logging.info(f"Получено сообщение: {user_input}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response['choices'][0]['message']['content']
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error("Ошибка при ответе GPT: %s", e)
        await update.message.reply_text("Ошибка при запросе к GPT.")

# === Регистрация хендлеров ===
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook endpoint ===
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        logging.error(f"❌ Ошибка webhook: {e}")
        return "error", 400

# === Запуск Flask + Telegram Application ===
if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.start()
        logging.info("🔗 Бот запущен и готов принимать обновления!")

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app.run(host="0.0.0.0", port=10000)
