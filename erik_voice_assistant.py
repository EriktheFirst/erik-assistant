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
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
webhook_url = f"https://erik-assistant.onrender.com/{TELEGRAM_TOKEN}"

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)


# Ответ от GPT
async def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "Ошибка при запросе к GPT."


# Хэндлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Ерик — твой ИИ-помощник.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    reply = await chatgpt_response(user_input)
    await update.message.reply_text(reply)


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Webhook-обработчик
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"❌ Ошибка во webhook: {e}")
        return "error", 400
    return "ok", 200


# Запуск бота + установка webhook
async def startup():
    await application.initialize()
    await application.start()
    # Установка webhook
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        data={"url": webhook_url}
    )
    print("✅ Webhook установлен:", webhook_url)


# Flask + Telegram
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    app.run(host="0.0.0.0", port=10000)
