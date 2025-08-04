import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import openai
import requests

# === Переменные окружения ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("✅ TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("✅ OPENAI_API_KEY:", OPENAI_API_KEY)

# === Flask-приложение ===
app = Flask(__name__)

# === Telegram бота и приложение ===
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === Установка ключа OpenAI ===
openai.api_key = OPENAI_API_KEY

# === Логгинг ===
logging.basicConfig(level=logging.INFO)

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# === Ответ от GPT ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        logging.info(f"📩 Получено сообщение: {user_input}")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response['choices'][0]['message']['content'].strip()
        await update.message.reply_text(reply)
        logging.info(f"🤖 Ответ отправлен: {reply}")
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")

# === Обработчики ===
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

# === Главный запуск ===
if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.start()
        logging.info("🚀 Бот запущен.")

        # === Автоматическая установка Webhook ===
        webhook_url = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            data={"url": webhook_url}
        )
        logging.info("📡 Webhook установлен: %s", res.text)

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app.run(host="0.0.0.0", port=10000)
