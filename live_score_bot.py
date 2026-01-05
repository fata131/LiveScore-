import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ================= ENV =================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("RAPIDAPI_KEY")

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# ================= STORAGE =================
favorites = {}
live_cache = {}

# ================= VIP =================
premium_users = {
    9167481626  # Lukmon Fatai Olamide
}

VIP_PAYMENT_TEXT = (
    "💎 *VIP ACCESS*\n\n"
    "Unlock premium features:\n"
    "✔ Faster goal alerts\n"
    "✔ Priority updates\n"
    "✔ Exclusive features\n\n"
    "💳 *Payment Details*\n"
    "Bank: Opay\n"
    "Name: Lukmon Fatai Olamide\n"
    "Account: 9167481626"
)

# ================= API FUNCTIONS =================
def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        return data.get("response", [])
    except:
        return []

def live_matches():
    games = safe_get(f"{BASE_URL}/fixtures?live=all")
    if not games:
        return "❌ No live matches now."

    msg = "🔥 *LIVE MATCHES*\n\n"
    for g in games[:10]:
        h = g["teams"]["home"]["name"]
        a = g["teams"]["away"]["name"]
        gh = g["goals"]["home"]
        ga = g["goals"]["away"]
        msg += f"{h} {gh} - {ga} {a}\n"
    return msg

def standings():
    table = safe_get(f"{BASE_URL}/standings?league=39&season=2024")
    if not table:
        return "❌ Standings unavailable."

    rows = table[0]["league"]["standings"][0][:6]
    msg = "📊 *EPL STANDINGS*\n\n"
    for t in rows:
        msg += f"{t['rank']}. {t['team']['name']} — {t['points']} pts\n"
    return msg

def scorers():
    players = safe_get(f"{BASE_URL}/players/topscorers?league=39&season=2024")
    if not players:
        return "❌ Data unavailable."

    msg = "⚽ *TOP SCORERS*\n\n"
    for p in players[:5]:
        msg += f"{p['player']['name']} — {p['statistics'][0]['goals']['total']}\n"
    return msg

# ================= UI =================
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
        ],
    ])

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *LiveScore Bot*\nReal-time football updates 👇",
        reply_markup=menu(),
        parse_mode="Markdown",
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
        teams = favorites.get(uid, [])
        text = "⭐ *Your Teams*\n\n" + ("\n".join(teams) if teams else "No teams added.")

    elif q.data == "add":
        context.user_data["add"] = True
        await q.edit_message_text("✍️ Send team name:")
        return

    elif q.data == "alerts":
        context.user_data["alert"] = True
        await q.edit_message_text("🔔 Send team name for alerts:")
        return

    elif q.data == "vip":
        text = "✅ VIP ACTIVE" if uid in premium_users else VIP_PAYMENT_TEXT

    else:
        text = "Updated."

    await q.edit_message_text(text, reply_markup=menu(), parse_mode="Markdown")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    if context.user_data.get("add"):
        favorites.setdefault(uid, []).append(text)
        context.user_data["add"] = False
        await update.message.reply_text(f"✅ {text} added.", reply_markup=menu())

    elif context.user_data.get("alert"):
        favorites.setdefault(uid, []).append(text)
        context.user_data["alert"] = False
        await update.message.reply_text(f"🔔 Alerts enabled for {text}.", reply_markup=menu())

# ================= GOAL ALERT JOB =================
async def goal_checker(context: ContextTypes.DEFAULT_TYPE):
    games = safe_get(f"{BASE_URL}/fixtures?live=all")
    if not games:
        return

    for g in games:
        fid = g["fixture"]["id"]
        score = f"{g['goals']['home']}-{g['goals']['away']}"

        if live_cache.get(fid) != score:
            live_cache[fid] = score
            for u, teams in favorites.items():
                if (
                    g["teams"]["home"]["name"] in teams
                    or g["teams"]["away"]["name"] in teams
                ):
                    await context.bot.send_message(
                        u,
                        f"⚽ GOAL!\n{g['teams']['home']['name']} {score} {g['teams']['away']['name']}"
                    )

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.job_queue.run_repeating(goal_checker, interval=60, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
