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

# Загрузка переменных окружения (на всякий случай)
load_dotenv()

# Получение токенов из переменных окружения Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("OPENAI_API_KEY:", OPENAI_API_KEY)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logging.getLogger("telegram.ext.application").setLevel(logging.DEBUG)

# Flask приложение для webhook
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Инициализация Telegram Application
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Установка ключа OpenAI
openai.api_key = OPENAI_API_KEY

# GPT-ответ
async def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error("Ошибка OpenAI: %s", e)
        return "Произошла ошибка при обработке запроса."

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        print("📩 Получено сообщение:", user_input)

        reply = await chatgpt_response(user_input)
        print("🤖 Ответ от GPT:", reply)

        await update.message.reply_text(reply)
        print("✅ Ответ отправлен пользователю")

    except Exception as e:
        print("❌ Ошибка в обработке сообщения:", str(e))
        await update.message.reply_text("Произошла ошибка. Попробуй снова позже.")

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook endpoint
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put_nowait(update)
        return "ok"
    except Exception as e:
        print("❌ Ошибка во webhook:", e)
        return "error", 400

# Асинхронный запуск Telegram-бота
async def run():
    await application.initialize()
    await application.start()

# Запуск Flask + Telegram одновременно
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run())
    app.run(host="0.0.0.0", port=10000)
