import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
app = Flask(__name__)

tg_app = ApplicationBuilder().token(TOKEN).build()

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

# --- Start bot in background ---
async def run_bot():
    await tg_app.initialize()
    await tg_app.start()

asyncio.get_event_loop().create_task(run_bot())

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    tg_app.update_queue.put_nowait(update)
    return "OK"

application = app
