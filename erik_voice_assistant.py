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

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка токенов
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN или OPENAI_API_KEY не установлены в переменных окружения")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Telegram Application
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# OpenAI ключ
openai.api_key = OPENAI_API_KEY

# Функция ответа через ChatGPT
async def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error("Ошибка OpenAI: %s", e)
        return "Произошла ошибка при обращении к GPT."

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        logger.info("📩 Получено сообщение: %s", user_input)
        reply = await chatgpt_response(user_input)
        await update.message.reply_text(reply)
        logger.info("✅ Ответ отправлен пользователю")
    except Exception as e:
        logger.error("Ошибка в обработке сообщения: %s", str(e))
        await update.message.reply_text("Произошла ошибка. Попробуй снова позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook endpoint
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.create_task(application.process_update(update))
        logger.info("📨 Update обработан: %s", update)
        return "ok"
    except Exception as e:
        logger.error("❌ Ошибка во webhook: %s", e)
        return "error", 400

# Установка Webhook при запуске
@app.before_first_request
def set_webhook():
    webhook_url = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        data={"url": webhook_url}
    )
    logger.info("📡 Установка Webhook: %s", response.text)

# Запуск Flask + Telegram
async def run():
    await application.initialize()
    await application.start()
    logger.info("🚀 Telegram-бот запущен")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run())
    app.run(host="0.0.0.0", port=10000)
