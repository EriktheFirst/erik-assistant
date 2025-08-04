import os
import asyncio
import logging
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
import openai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_URL = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"

# Логгинг
logging.basicConfig(level=logging.INFO)

# Flask и Telegram App
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
openai.api_key = OPENAI_API_KEY

# Обработчик сообщений
async def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "Произошла ошибка при обращении к ChatGPT."

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logging.info(f"Получено сообщение: {user_input}")
    reply = await chatgpt_response(user_input)
    await update.message.reply_text(reply)

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook route
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK"

# Запуск приложения
if __name__ == "__main__":
    # Установка webhook
    webhook_url = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"
    set_hook = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        data={"url": webhook_url}
    )
    logging.info("Webhook установлен: %s", set_hook.text)

    loop = asyncio.get_event_loop()
    loop.create_task(application.initialize())
    loop.create_task(application.start())
    app.run(host="0.0.0.0", port=10000)
