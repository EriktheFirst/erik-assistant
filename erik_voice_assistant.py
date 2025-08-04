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

# Загрузка .env (на всякий случай, Render может не использовать, но локально — нужно)
load_dotenv()

# Получение токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН_ЕСЛИ_НУЖНО"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "sk-..."

# Проверка
print("✅ TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("✅ OPENAI_API_KEY:", OPENAI_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Telegram application
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
openai.api_key = OPENAI_API_KEY

# GPT ответ
async def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "Произошла ошибка при обращении к ChatGPT."

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    print("📥 Сообщение:", user_input)
    reply = await chatgpt_response(user_input)
    print("📤 Ответ:", reply)
    await update.message.reply_text(reply)

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Явно прописываем URL Webhook — Telegram будет стучаться сюда!
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put_nowait(update)
        return "ok"
    except Exception as e:
        print("❌ Ошибка webhook:", e)
        return "error", 400

# Асинхронный запуск Telegram-бота
async def run_bot():
    await application.initialize()
    await application.start()
    print("✅ Бот запущен (через webhook)")

# Запуск Flask и Telegram
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    app.run(host="0.0.0.0", port=10000)
