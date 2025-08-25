import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"  # or use os.getenv("TELEGRAM_TOKEN")

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔍 Inline Test", callback_data="test")]]
    await update.message.reply_text("🧪 Inline button test:", reply_markup=InlineKeyboardMarkup(kb))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await context.bot.send_message(chat_id=q.message.chat.id, text=f"✅ You tapped: {q.data}")

# --- Main runner ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    await app.run_polling()

# --- Entry point ---
if __name__ == "__main__":
    asyncio.run(main())
s
