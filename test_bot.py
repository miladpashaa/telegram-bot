import os
import asyncio
import threading
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

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

# --- Background thread to run bot loop ---
def run_bot():
    asyncio.run(_run_bot())

async def _run_bot():
    await tg_app.initialize()
    await tg_app.start()
    # Idle forever so the bot stays running
    await tg_app.updater.start_polling()  # <- or tg_app.updater.start_webhook(...) if using webhook

threading.Thread(target=run_bot, daemon=True).start()

# --- Webhook endpoint ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.update_queue.put(update))
    return "OK"

# Gunicorn entrypoint
application = app
