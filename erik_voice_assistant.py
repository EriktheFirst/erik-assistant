import os
import logging
import asyncio

from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# 🔹 Настройка логов
logging.basicConfig(level=logging.INFO)

# 🔹 Создание Flask-приложения
app = Flask(__name__)

# 🔹 Получение токена из переменных окружения (Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 🔹 Создание telegram-приложения
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()


# 🔹 Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я жив!")

application.add_handler(CommandHandler("start", start))


# 🔹 Инициализация Telegram-бота перед первым запросом
@app.before_serving
async def init_bot():
    await application.initialize()
    await application.start()
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}"
    await application.bot.set_webhook(webhook_url)
    logging.info(f"📡 Webhook установлен: {webhook_url}")


# 🔹 Обработка входящих webhook-запросов от Telegram
@app.post(f"/{TELEGRAM_TOKEN}")
async def webhook_handler():
    try:
        update = Update.de_json(request.json, application.bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"❌ Ошибка во webhook: {e}")
        return "error", 400
    return "ok", 200


# 🔹 Точка входа
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
