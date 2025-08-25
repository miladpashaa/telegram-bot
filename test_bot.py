import os
import threading
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
app = Flask(__name__)

tg_app = ApplicationBuilder().token(TOKEN).build()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔍 Inline Test", callback_data="test")]]
    await update.message.reply_text("🧪 Inline button test:", reply_markup=InlineKeyboardMarkup(kb))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await context.bot.send_message(chat_id=q.message.chat.id, text=f"✅ You tapped: {q.data}")

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(on_callback))

# --- Background bot runner ---
def run_bot():
    asyncio.run(bot_loop())

async def bot_loop():
    webhook_url = f"{os.getenv('WEBHOOK_BASE')}/webhook"
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path="webhook",
        webhook_url=webhook_url
    )
    await tg_app.updater.idle()

threading.Thread(target=run_bot, daemon=True).start()

# --- Webhook endpoint for Flask ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.get_event_loop().create_task(tg_app.update_queue.put(update))
    return "OK"

application = app
