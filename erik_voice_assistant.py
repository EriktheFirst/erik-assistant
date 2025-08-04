import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import requests

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask
app = Flask(__name__)

# Токены из Render env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Асинхронный обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        reply = await chatgpt_response(user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error("Handle message error: %s", e)
        await update.message.reply_text("Ошибка при обработке сообщения.")

# Получение ответа от GPT
async def chatgpt_response(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("OpenAI error: %s", e)
        return "Ошибка при обращении к OpenAI."

# Создание Telegram приложения
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook Flask
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.get_event_loop().create_task(application.process_update(update))
    return "OK"

# Установка Webhook при запуске
@app.before_first_request
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}"
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", data={"url": url})
    logging.info("Webhook set: %s", r.text)

# Старт Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
