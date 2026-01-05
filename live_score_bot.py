import os, requests, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("RAPIDAPI_KEY")

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

BASE = "https://api-football-v1.p.rapidapi.com/v3"

favorites = {}
alerts = {}
live_cache = {}

VIP_USERS = set()  # add telegram IDs later

# ---------- UI ----------
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Live", callback_data="live"),
         InlineKeyboardButton("📰 News", callback_data="news")],

        [InlineKeyboardButton("📊 Standings", callback_data="standings"),
         InlineKeyboardButton("⚽ Scorers", callback_data="scorers")],

        [InlineKeyboardButton("⭐ My Teams", callback_data="teams"),
         InlineKeyboardButton("➕ Add Team", callback_data="add")],

        [InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
         InlineKeyboardButton("📋 Match Details", callback_data="details")],

        [InlineKeyboardButton("💎 VIP Zone", callback_data="vip"),
         InlineKeyboardButton("🔄 Refresh", callback_data="refresh")]
    ])

# ---------- DATA ----------
def live_matches():
    r = requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS).json()["response"]
    if not r: return "❌ No live matches"
    msg = "🔥 LIVE MATCHES\n\n"
    for m in r[:8]:
        msg += f"{m['teams']['home']['name']} {m['goals']['home']} - {m['goals']['away']} {m['teams']['away']['name']}\n"
    return msg

def standings():
    r = requests.get(f"{BASE}/standings?league=39&season=2024", headers=HEADERS).json()
    table = r["response"][0]["league"]["standings"][0][:6]
    return "\n".join([f"{t['rank']}. {t['team']['name']} ({t['points']} pts)" for t in table])

def scorers():
    r = requests.get(f"{BASE}/players/topscorers?league=39&season=2024", headers=HEADERS).json()["response"][:5]
    return "\n".join([f"{p['player']['name']} - {p['statistics'][0]['goals']['total']}" for p in r])

def news():
    r = requests.get(f"{BASE}/fixtures?next=5", headers=HEADERS).json()["response"]
    msg = "📰 UPCOMING MATCHES\n\n"
    for m in r:
        msg += f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}\n"
    return msg

# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *LiveScore Bot*\nReal-time football updates 👇",
        reply_markup=menu(),
        parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "live": text = live_matches()
    elif q.data == "standings": text = standings()
    elif q.data == "scorers": text = scorers()
    elif q.data == "news": text = news()

    elif q.data == "teams":
        text = "⭐ Your Teams:\n" + "\n".join(favorites.get(uid, [])) if uid in favorites else "No teams yet"

    elif q.data == "add":
        context.user_data["add"] = True
        await q.edit_message_text("✍️ Send team name:")
        return

    elif q.data == "alerts":
        context.user_data["alert"] = True
        await q.edit_message_text("🔔 Send team for alerts:")
        return

    elif q.data == "details":
        text = "📋 Tap Live to view match details."

    elif q.data == "vip":
        text = (
            "💎 VIP ZONE\n\n"
            "Unlock premium features\n\n"
            "💰 PAYMENT DETAILS\n"
            "Bank: Opay\n"
            "Name: Lukmon Fatai Olamide\n"
            "Account: 9167481626\n\n"
            "After payment, contact admin."
        )

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
        alerts.setdefault(uid, []).append(txt)
        context.user_data["alert"] = False
        await update.message.reply_text(f"🔔 Alert set for {txt}", reply_markup=menu())

# ---------- GOAL ALERT ----------
async def goal_loop(app):
    while True:
        r = requests.get(f"{BASE}/fixtures?live=all", headers=HEADERS).json()["response"]
        for g in r:
            fid = g["fixture"]["id"]
            score = f"{g['goals']['home']}-{g['goals']['away']}"
            if live_cache.get(fid) != score:
                live_cache[fid] = score
                for u, t in alerts.items():
                    if g["teams"]["home"]["name"] in t or g["teams"]["away"]["name"] in t:
                        await app.bot.send_message(u, f"⚽ GOAL!\n{g['teams']['home']['name']} {score} {g['teams']['away']['name']}")
        await asyncio.sleep(60)

# ---------- MAIN ----------
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    asyncio.create_task(goal_loop(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
