import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= ENV =================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

FOOTBALL_HEADERS = {
    "x-rapidapi-key": FOOTBALL_API_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

FOOTBALL_BASE = "https://api-football-v1.p.rapidapi.com/v3"

# ================= BUTTON UI (BOTTOM) =================
keyboard = ReplyKeyboardMarkup(
    [
        ["⚽ Live Scores", "🏆 Leagues"],
        ["⭐ My Team", "📊 Standings"],
        ["🤖 AI Chat", "ℹ️ Help"]
    ],
    resize_keyboard=True
)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *LiveScore Bot*\n\nChoose an option below 👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ================= LIVE SCORES =================
def get_live_scores():
    r = requests.get(f"{FOOTBALL_BASE}/fixtures?live=all", headers=FOOTBALL_HEADERS)
    data = r.json().get("response", [])

    if not data:
        return "❌ No live matches now."

    text = "🔥 LIVE MATCHES\n\n"
    for m in data[:10]:
        h = m["teams"]["home"]["name"]
        a = m["teams"]["away"]["name"]
        g = m["goals"]
        text += f"{h} {g['home']} - {g['away']} {a}\n"

    return text

# ================= LEAGUES =================
def get_leagues():
    r = requests.get(f"{FOOTBALL_BASE}/leagues", headers=FOOTBALL_HEADERS)
    leagues = r.json().get("response", [])[:15]

    text = "🏆 TOP LEAGUES\n\n"
    for l in leagues:
        text += f"{l['league']['name']} ({l['country']['name']})\n"

    return text

# ================= STANDINGS =================
def get_standings():
    r = requests.get(
        f"{FOOTBALL_BASE}/standings?league=39&season=2024",
        headers=FOOTBALL_HEADERS
    )
    table = r.json()["response"][0]["league"]["standings"][0][:10]

    text = "📊 EPL STANDINGS\n\n"
    for t in table:
        text += f"{t['rank']}. {t['team']['name']} - {t['points']} pts\n"

    return text

# ================= AI CHAT =================
def ai_chat(prompt):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "⚽ Live Scores":
        await update.message.reply_text(get_live_scores())

    elif text == "🏆 Leagues":
        await update.message.reply_text(get_leagues())

    elif text == "📊 Standings":
        await update.message.reply_text(get_standings())

    elif text == "⭐ My Team":
        await update.message.reply_text("Feature active soon ✅")

    elif text == "🤖 AI Chat":
        context.user_data["ai"] = True
        await update.message.reply_text("🤖 Ask me anything:")

    elif context.user_data.get("ai"):
        reply = ai_chat(text)
        await update.message.reply_text(reply)

    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Use buttons below 👇\nLive scores • leagues • AI chat"
        )

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
