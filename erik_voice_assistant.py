import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменной среды (Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")

# Flask-приложение
app = Flask(__name__)

# Telegram Bot Application
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Erik Assistant.")

# Ответ на обычные сообщения
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Добавление обработчиков
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Webhook endpoint
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        asyncio.run(bot_app.process_update(update))
    except Exception as e:
        logger.error("\u274c Ошибка во webhook: %s", e)
    return "ok"

# Установка Webhook
async def set_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TELEGRAM_TOKEN}"
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.set_webhook(url=webhook_url)
    logger.info("\ud83d\udce1 Webhook установлен: %s", webhook_url)

# Инициализация
async def init_bot():
    await set_webhook()

# Запуск
if __name__ == '__main__':
    asyncio.run(init_bot())
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
