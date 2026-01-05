import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")   # Your Telegram bot token
SPORTDB_KEY = os.getenv("SPORTDB_KEY")        # Your SportDB API key

HEADERS = {
    "X-API-Key": SPORTDB_KEY
}

BASE_URL = "https://api.sportdb.dev/api/flashscore"

# ---------------- STORAGE ----------------
favorites = {}      # User favorite teams
live_cache = {}     # Keep track of last score to prevent duplicate alerts

# VIP USERS
premium_users = {
    9167481626  # Lukmon Fatai Olamide (VIP)
}

# ---------------- API ----------------
def live_matches():
    try:
        r = requests.get(f"{BASE_URL}/", headers=HEADERS, timeout=10).json()
        matches = r.get("matches", [])
        if not matches:
            return "❌ No live matches now."

        msg = "🔥 LIVE MATCHES\n\n"
        for m in matches[:8]:
            h = m["home"]["name"]
            a = m["away"]["name"]
            g = m.get("score", {})
            msg += f"{h} {g.get('home', 0)} - {g.get('away', 0)} {a}\n"
        return msg
    except Exception as e:
        return f"❌ Error fetching live matches: {e}"

# ---------------- UI BUTTONS ----------------
def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Live", callback_data="live"),
            InlineKeyboardButton("⭐ My Teams", callback_data="teams")
        ],
        [
            InlineKeyboardButton("➕ Add Team", callback_data="add"),
            InlineKeyboardButton("🔔 Goal Alerts", callback_data="alerts")
        ],
        [
            InlineKeyboardButton("💎 VIP Zone", callback_data="vip"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
        ]
    ])

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *LiveScore Bot*\nReal football updates below 👇",
        reply_markup=menu(),
        parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "live":
        text = live_matches()

    elif q.data == "teams":
        t = favorites.get(uid, [])
        text = "⭐ Your Teams:\n" + ("\n".join(t) if t else "No teams yet.")

    elif q.data == "add":
        context.user_data["add"] = True
        await q.edit_message_text("✍️ Send team name:")
        return

    elif q.data == "alerts":
        context.user_data["alert"] = True
        await q.edit_message_text("🔔 Send team for alerts:")
        return

    elif q.data == "vip":
        if uid in premium_users:
            text = "💎 VIP ACTIVE\n✔ Fast alerts\n✔ Priority updates\n✔ Exclusive features"
        else:
            text = "🔒 VIP ONLY\nContact admin to upgrade."

    else:
        text = "Updated."

    await q.edit_message_text(text, reply_markup=menu())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    txt = update.message.text.strip()

    if context.user_data.get("add"):
        favorites.setdefault(uid, []).append(txt)
        context.user_data["add"] = False
        await update.message.reply_text(f"✅ {txt} added", reply_markup=menu())

    elif context.user_data.get("alert"):
        favorites.setdefault(uid, []).append(txt)
        context.user_data["alert"] = False
        await update.message.reply_text(f"🔔 Alerts set for {txt}", reply_markup=menu())

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Run the bot (this handles async loop internally)
    app.run_polling()

if __name__ == "__main__":
    main()
