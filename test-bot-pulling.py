# bazarroz_bot.py

import os
import logging
import asyncio
import threading
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, request
import aiohttp
import pandas as pd
import requests

from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------- Env & logging ----------
load_dotenv()
TOKEN        = (os.getenv("TELEGRAM_TOKEN") or "").strip()
SECRET_TOKEN = (os.getenv("SECRET_TOKEN") or "").strip()
WEBHOOK_BASE = (os.getenv("WEBHOOK_BASE") or "").strip()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    force=True,
)
log = logging.getLogger("bazarroz-bot")

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN in .env")
if not SECRET_TOKEN:
    raise RuntimeError("Missing SECRET_TOKEN in .env")
if not WEBHOOK_BASE:
    raise RuntimeError(
        "Missing WEBHOOK_BASE in .env (e.g., https://<username>.pythonanywhere.com)"
    )

log.info("TELEGRAM_TOKEN length: %d", len(TOKEN))
log.info("TELEGRAM_TOKEN starts with: %s", TOKEN[:10])

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# ---------- Real API endpoints ----------
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
CRYPTO_API = os.getenv("CRYPTO_API_KEY")
GOLD_API = os.getenv("GOLD_API_KEY")


# ---------- State ----------
bot_data: List[Any] = []  # for /excel_file snapshots
# ---------- Helpers ----------
async def get_crypto_data() -> Optional[List[Dict[str, Any]]]:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(CRYPTO_API, timeout=20) as resp:
                d = await resp.json()
                return d.get("data") if d else None
    except Exception as e:
        log.error("get_crypto_data error: %s", e)
        return None

async def fetch_gold_data() -> Optional[Dict[str, Any]]:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(GOLD_API, timeout=20) as resp:
                return await resp.json()
    except Exception as e:
        log.error("fetch_gold_data error: %s", e)
        return None

async def top_crypto_text(data: List[Dict[str, Any]]) -> str:
    lines, last_dt = [], None
    for i, c in enumerate(data[:25]):
        lines += [
            f"{i+1}💰 {c.get('title','')}",
            f"({c.get('symbol','')})💲: {c.get('p','')} - IR{c.get('p_irr','')}",
            f"volume📊: {c.get('volume','')}",
            "***********************************",
        ]
        last_dt = c.get("datetime", last_dt)
    if last_dt:
        lines.append(f"⏲️ {last_dt}")
    return "\n".join(lines) if lines else "No crypto data to show."

# ---------- Command handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("قیمت کدوم بازار می‌خوای؟\n/menu برای دکمه‌ها")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_crypto_data()
    if data:
        bot_data.append(data)
        await update.message.reply_text(await top_crypto_text(data))
    else:
        await update.message.reply_text("Failed to retrieve data.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_crypto_data()
    symbol = "-".join(context.args) if context.args else ""
    if not symbol:
        return await update.message.reply_text("example... /search BTC")
    if not data:
        return await update.message.reply_text("Failed to retrieve data.")
    filtered = [c for c in data if symbol.upper() in c.get("symbol","")]
    if not filtered:
        return await update.message.reply_text(f'"{symbol}" not found.')
    lines = []
    for c in filtered:
        cr = c.get("cr", {})
        lines += [
            f"⏲️ {c.get('datetime','')}",
            f"💰 {c.get('title','')} {c.get('symbol','')}",
            f"💲{c.get('p','')}\nIR: {c.get('p_irr','')}",
            f"change: {c.get('d','')}",
            f"change%: {c.get('dp','')}",
            f"highest-24h: {cr.get('highest-24h-usd','')}",
            f"highest-7d: {cr.get('highest-7d-usd','')}",
            f"volume📊: {c.get('volume','')}",
            f"volatility: {cr.get('volatility-usd','')}",
            "***********************************",
        ]
    await update.message.reply_text("\n".join(lines))

# Gold & currency handlers (copied unchanged from your two parts)
# ... (goldons, goldprice, seke_retails, sekee, stockm_gold, stockm_seke,
#       a_currencies, a_currency, e_currencies, excel_file) ...

async def goldons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]
            blk = n["ons"]
            lines = [
                f"اُنس    {blk.get('t','')}\n{blk.get('ts','')}",
                f"طلا: {blk.get('p','')}",
                f"نقره: {n.get('silver',{}).get('p','')}",
                f"پلاتینیوم: {n.get('platinum',{}).get('p','')}",
                f"پالادیوم: {n.get('palladium',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def goldprice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]
            g18 = n.get("geram18",{})
            lines = [
                f"قیمت طلا {g18.get('t','')}\n{g18.get('ts','')}",
                f"18 ایار: {g18.get('p','')}",
                f"24 ایار: {n.get('geram24',{}).get('p','')}",
                f"مثقال: {n.get('mesghal',{}).get('p','')}",
                f"آب شد: {n.get('gold_17_transfer',{}).get('p','')}",
                f"حباب آب شد: {n.get('gold_futures',{}).get('p','')}",
                f"مثقال بدون حباب: {n.get('gold_17',{}).get('p','')}",
                f"طلا دسته دوم: {n.get('gold_mini_size',{}).get('p','')}",
                f"گرم نقره 999: {n.get('silver_999',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def seke_retails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]["retail_sekee"]
            r  = d["current"]
            lines = [
                f"سکه تک فروشی   {n.get('t','')}\n{n.get('ts','')}",
                f"امام: {n.get('p','')}",
                f"بهارآزادی: {r.get('retail_sekeb',{}).get('p','')}",
                f"نیم: {r.get('retail_nim',{}).get('p','')}",
                f"ربع: {r.get('retail_rob',{}).get('p','')}",
                f"گرمی: {r.get('retail_gerami',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def sekee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]["sekee"]
            r = d["current"]
            title = n.get("t") or n.get("t-g","")
            lines = [
                f"سکه   {title}\n{n.get('ts','')}",
                f"امام: {n.get('p','')}",
                f"بهارآزادی: {r.get('sekeb',{}).get('p','')}",
                f"نیم: {r.get('nim',{}).get('p','')}",
                f"ربع: {r.get('rob',{}).get('p','')}",
                f"گرمی: {r.get('gerami',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def stockm_gold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]["gc10"]
            r = d["current"]
            lines = [
                f"صندوق های طلا در بورس  {n.get('t','')}\n{n.get('ts','')}",
                f"گوهر: {n.get('p','')}",
                f"لوتوس: {r.get('gc1',{}).get('p','')}",
                f"مفید: {r.get('gc3',{}).get('p','')}",
                f"زر: {r.get('gc11',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def stockm_seke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            n = d["current"]["gc19"]
            r = d["current"]
            lines = [
                f"تمام سکه {n.get('t','')}\n{n.get('ts','')}",
                f"صادرات: {n.get('p','')}",
                f"آینده: {r.get('gc18',{}).get('p','')}",
                f"سامان: {r.get('gc17',{}).get('p','')}",
                f"رفاه: {r.get('gc15',{}).get('p','')}",
                f"ملت: {r.get('gc14',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def a_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            hdr = d["current"]["price_cny"]
            lines = [
                f"ارز کشورهای آسیایی: {hdr.get('t','')}\n{hdr.get('ts','')}",
                f"یوان چین: {d['current'].get('price_cny',{}).get('p','')}",
                f"روبل روسیه: {d['current'].get('price_rub',{}).get('p','')}",
                f"ین ژاپن: {d['current'].get('price_jpy',{}).get('p','')}",
                f"وون کره: {d['current'].get('price_krw',{}).get('p','')}",
                f"دلار هنگ کنگ: {d['current'].get('price_hkd',{}).get('p','')}",
                f"دلار سنگاپور: {d['current'].get('price_sgd',{}).get('p','')}",
                f"رینگیت مالزی: {d['current'].get('price_myr',{}).get('p','')}",
                f"لیر ترکیه: {d['current'].get('price_try',{}).get('p','')}",
                f"بات تایلند: {d['current'].get('price_thb',{}).get('p','')}",
                f"افغانی: {d['current'].get('price_afn',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def a_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            hdr = d["current"]["price_iqd"]
            lines = [
                f"کشورهای عربی خلیج فارس: {hdr.get('t','')}\n{hdr.get('ts','')}",
                f"ریال عربستان: {d['current'].get('price_sar',{}).get('p','')}",
                f"ریال قطر: {d['current'].get('price_qar',{}).get('p','')}",
                f"ریال عمان: {d['current'].get('price_omr',{}).get('p','')}",
                f"دینار کویت: {d['current'].get('price_kwd',{}).get('p','')}",
                f"دینار بحرین: {d['current'].get('price_bhd',{}).get('p','')}",
                f"دینار عراق: {d['current'].get('price_iqd',{}).get('p','')}",
                f"لیر سوریه: {d['current'].get('price_syp',{}).get('p','')}",
                f"درهم امارات: {d['current'].get('price_aed',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def e_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "No data found."
    d = await fetch_gold_data()
    if d:
        try:
            hdr = d["current"]["price_dollar_rl"]
            lines = [
                f"کشورهای غرب:    {hdr.get('t','')}\n{hdr.get('ts','')}",
                f"دلار: {hdr.get('p','')}",
                f"یورو: {d['current'].get('price_eur',{}).get('p','')}",
                f"پوند انگلیس: {d['current'].get('price_gbp',{}).get('p','')}",
                f"فرانک سویس: {d['current'].get('price_chf',{}).get('p','')}",
                f"دلار کانادا: {d['current'].get('price_cad',{}).get('p','')}",
                f"دلار استرالیا: {d['current'].get('price_aud',{}).get('p','')}",
                f"دلار نیوزلند: {d['current'].get('price_nzd',{}).get('p','')}",
            ]
            msg = "\n".join(lines)
        except KeyError:
            pass
    await update.message.reply_text(msg)

async def excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows: List[Dict[str, Any]] = []
    for snap in bot_data:
        if isinstance(snap, list):
            rows.extend(snap)
        elif isinstance(snap, dict):
            rows.append(snap)
    if not rows:
        return await update.message.reply_text("No data captured yet. Use /top first.")
    df = pd.DataFrame(rows)
    df.to_excel("telegram_bot_data.xlsx", index=False)
    await update.message.reply_text("دریافت اکسل: telegram_bot_data.xlsx")

# ---------- Menu & Callback ---------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("شروع", callback_data="start")],
        [InlineKeyboardButton("برترین‌ها در کریپتو", callback_data="top")],
        [InlineKeyboardButton("ارز مورد نظرت", callback_data="search")],
        [InlineKeyboardButton("اُنس طلا", callback_data="goldons")],
        [InlineKeyboardButton("قیمت طلا", callback_data="goldprice")],
        [InlineKeyboardButton("سکه تک فروشی", callback_data="seke_retails")],
        [InlineKeyboardButton("سکه", callback_data="sekee")],
        [InlineKeyboardButton("طلا در بورس", callback_data="stockm_gold")],
        [InlineKeyboardButton("سکه در بورس", callback_data="stockm_seke")],
        [InlineKeyboardButton("کشورهای آسیایی", callback_data="a_currencies")],
        [InlineKeyboardButton("حاشیه خلیج فارس", callback_data="a_currency")],
        [InlineKeyboardButton("کشورهای غربی", callback_data="e_currencies")],
        [InlineKeyboardButton("دریافت اکسل", callback_data="excel_file")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message( chat_id=update.effective_chat.id, text="یک گزینه را انتخاب کنید:", reply_markup=markup
)
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q    = update.callback_query
    data = (q.data or "").strip()

    # Debug: confirm PTB received the callback
    log.info("💡 PTB on_callback fired with data=%s", data)

    # Acknowledge the button tap immediately
    await q.answer()

    # Redirect update.message so your command handlers work unchanged
    update.message = q.message

    # Dispatch to your existing handlers
    if data == "start":
        await start(update, context)
    elif data == "top":
        await top(update, context)
    elif data == "search":
        await context.bot.send_message(
            chat_id=q.message.chat.id,
            text="برای جستجو، دستور /search <نام ارز> را بزنید"
        )
    elif data == "goldons":
        await goldons(update, context)
    elif data == "goldprice":
        await goldprice(update, context)
    elif data == "seke_retails":
        await seke_retails(update, context)
    elif data == "sekee":
        await sekee(update, context)
    elif data == "stockm_gold":
        await stockm_gold(update, context)
    elif data == "stockm_seke":
        await stockm_seke(update, context)
    elif data == "a_currencies":
        await a_currencies(update, context)
    elif data == "a_currency":
        await a_currency(update, context)
    elif data == "e_currencies":
        await e_currencies(update, context)
    elif data == "excel_file":
        await excel_file(update, context)
    else:
        # Fallback / help text
        await context.bot.send_message(
            chat_id=q.message.chat.id,
            text=(
                "📜 راهنما:\n"
                "/start – شروع\n"
                "/menu – نمایش دکمه‌ها\n"
                "/top – رمزارزهای برتر\n"
                "/search <SYM> – جستجو\n"
                "/goldons /goldprice /seke_retails /sekee\n"
                "/stockm_gold /stockm_seke\n"
                "/a_currencies /a_currency /e_currencies\n"
                "/excel_file – دریافت اکسل"
            )
        )


# ---------- Build PTB app ----------
tg_app = ApplicationBuilder().token(TOKEN).build()
tg_app.add_handler(CommandHandler("menu", menu))
# Register command handlers
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("menu", menu))
tg_app.add_handler(CommandHandler("top", top))
tg_app.add_handler(CommandHandler("search", search))
tg_app.add_handler(CommandHandler("goldons", goldons))
tg_app.add_handler(CommandHandler("goldprice", goldprice))
tg_app.add_handler(CommandHandler("seke_retails", seke_retails))
tg_app.add_handler(CommandHandler("sekee", sekee))
tg_app.add_handler(CommandHandler("stockm_gold", stockm_gold))
tg_app.add_handler(CommandHandler("stockm_seke", stockm_seke))
tg_app.add_handler(CommandHandler("a_currencies", a_currencies))
tg_app.add_handler(CommandHandler("a_currency", a_currency))
tg_app.add_handler(CommandHandler("e_currencies", e_currencies))
tg_app.add_handler(CommandHandler("excel_file", excel_file))

# Register callback handler
tg_app.add_handler(CallbackQueryHandler(on_callback))

# ---------- Background loop for PTB ----------
_loop = asyncio.new_event_loop()
def _run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
threading.Thread(target=_run_loop, args=(_loop,), daemon=True).start()

async def _startup():
    await tg_app.initialize()
    await tg_app.start()
    # Auto-set webhook
    url = f"{WEBHOOK_BASE}/webhook"
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/setWebhook",
            json={
                "url": url,
                "secret_token": SECRET_TOKEN,
                "allowed_updates": ["message", "edited_message", "callback_query"],
                "max_connections": 40,
            },
            timeout=10,
        )
        log.info("setWebhook status=%s body=%s", resp.status_code, resp.text)
    except Exception as e:
        log.error("Failed to setWebhook: %s", e)
    log.info("✅ PTB startup coroutine scheduled")
asyncio.run_coroutine_threadsafe(_startup(), _loop)

# ---------- Flask app & webhook endpoint ----------
app = Flask(__name__)

@app.get("/")
def health():
    return "Bot is running."

@app.post("/webhook")
def webhook():
    # 1) Validate secret header
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET_TOKEN:
        log.warning("Rejected webhook: invalid secret token")
        return "forbidden", 403

    # 2) Parse incoming JSON
    update_json = request.get_json(silent=True) or {}

    # 3) Debug logs: messages vs. callbacks vs. others
    if "callback_query" in update_json:
        log.info("💡 FLASK got callback_query: %s", update_json["callback_query"])
    elif "message" in update_json:
        log.info("💡 FLASK got message update: %s", update_json["message"])
    else:
        log.info("💡 FLASK got other update type: %s", update_json)

    # 4) Hand off to PTB
    try:
        upd = Update.de_json(update_json, tg_app.bot)
        asyncio.run_coroutine_threadsafe(tg_app.process_update(upd), _loop)
    except Exception as e:
        log.exception("Failed to enqueue update to PTB: %s", e)

    # 5) Always acknowledge fast
    return "ok", 200

# WSGI entrypoint
application = app
