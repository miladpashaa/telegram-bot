import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
app = Flask(__name__)
tg_app = ApplicationBuilder().token(TOKEN).build()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 Inline Test", callback_data="test")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🧪 Inline button test:", reply_markup=markup)

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await context.bot.send_message(chat_id=q.message.chat.id, text=f"✅ You tapped: {q.data}")

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(on_callback))

# --- Background startup ---
async def start_bot():
    await tg_app.initialize()
    await tg_app.start()

# Schedule the bot to start when the event loop begins
asyncio.get_event_loop().create_task(start_bot())

# --- Webhook endpoint ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.update_queue.put(update))
    return "OK"

# Gunicorn entrypoint
application = app
