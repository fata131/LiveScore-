import os
import requests
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Put your bot token here if env not set
API_KEY = "5f0Bobb0bANiPW2rltZDOCFa8NUNVBmkVcyNzbjx"

HEADERS = {
    "X-API-Key": API_KEY
}

BASE_URL = "https://api.sportdb.dev/api/flashscore/"

# ---------------- STORAGE ----------------
favorites = {}
live_cache = {}

# VIP USERS
premium_users = {
    9167481626  # Lukmon Fatai Olamide (VIP)
}

# ---------------- API ----------------

def live_matches():
    try:
        r = requests.get(f"{BASE_URL}live", headers=HEADERS, timeout=10).json()
        matches = r.get("matches", [])
        if not matches:
            return "❌ No live matches now."

        msg = "🔥 LIVE MATCHES\n\n"
        for m in matches[:8]:
            h = m["home_team"]
            a = m["away_team"]
            score = f"{m.get('home_score','0')}-{m.get('away_score','0')}"
            msg += f"{h} {score} {a}\n"
        return msg
    except Exception as e:
        return f"❌ Error fetching live matches.\n{e}"

def standings():
    try:
        r = requests.get(f"{BASE_URL}standings", headers=HEADERS, timeout=10).json()
        table = r.get("standings", [])[:6]
        msg = "📊 LEAGUE STANDINGS\n\n"
        for t in table:
            msg += f"{t['position']}. {t['team']} - {t['points']} pts\n"
        return msg
    except:
        return "❌ Error fetching standings."

def scorers():
    try:
        r = requests.get(f"{BASE_URL}scorers", headers=HEADERS, timeout=10).json()
        top = r.get("scorers", [])[:5]
        msg = "⚽ TOP SCORERS\n\n"
        for p in top:
            msg += f"{p['player']} - {p['goals']} goals\n"
        return msg
    except:
        return "❌ Error fetching top scorers."

# ---------------- UI (BUTTONS) ----------------

def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Live", callback_data="live"),
            InlineKeyboardButton("📊 Standings", callback_data="standings"),
        ],
        [
            InlineKeyboardButton("⚽ Scorers", callback_data="scorers"),
            InlineKeyboardButton("⭐ My Teams", callback_data="teams"),
        ],
        [
            InlineKeyboardButton("➕ Add Team", callback_data="add"),
            InlineKeyboardButton("🔔 Goal Alerts", callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("💎 VIP Zone", callback_data="vip"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
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
    elif q.data == "standings":
        text = standings()
    elif q.data == "scorers":
        text = scorers()
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
            text = "💎 VIP ACTIVE\n\n✔ Fast alerts\n✔ Priority updates\n✔ Exclusive features"
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

# ---------------- GOAL ALERT LOOP ----------------

async def goal_checker(app):
    while True:
        try:
            r = requests.get(f"{BASE_URL}live", headers=HEADERS, timeout=10).json()
            games = r.get("matches", [])

            for g in games:
                fid = g["id"]
                score = f"{g.get('home_score',0)}-{g.get('away_score',0)}"
                if live_cache.get(fid) != score:
                    live_cache[fid] = score
                    for u, teams in favorites.items():
                        if g["home_team"] in teams or g["away_team"] in teams:
                            await app.bot.send_message(
                                u,
                                f"⚽ GOAL!\n{g['home_team']} {score} {g['away_team']}"
                            )
        except:
            pass
        await asyncio.sleep(60)

# ---------------- MAIN ----------------

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Start goal checker loop
    asyncio.create_task(goal_checker(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
