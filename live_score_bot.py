import os
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # already set on Railway
FOOTBALL_API_KEY = "13c68bc4d00c421d41dae0288e21b60a"
AI_API_KEY = "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"

API_FOOTBALL_URL = "https://v3.football.api-sports.io"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(level=logging.INFO)

# ================= KEYBOARD =================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("⚽ Live Scores"), KeyboardButton("🏆 Leagues")],
        [KeyboardButton("⭐ My Team"), KeyboardButton("📊 Standings")],
        [KeyboardButton("🤖 AI Chat"), KeyboardButton("ℹ️ Help")]
    ],
    resize_keyboard=True
)

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 *Kings LiveScore Bot*\n\n"
        "Live scores • leagues • AI chat\n\n"
        "Use buttons below 👇",
        reply_markup=MAIN_KEYBOARD,
        parse_mode="Markdown"
    )

# ================= FOOTBALL =================
def football_api(endpoint, params=None):
    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }
    r = requests.get(f"{API_FOOTBALL_URL}/{endpoint}", headers=headers, params=params)
    return r.json()

async def live_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = football_api("fixtures", {"live": "all"})
    fixtures = data.get("response", [])

    if not fixtures:
        await update.message.reply_text("❌ No live matches now.")
        return

    msg = "🔥 *Live Matches*\n\n"
    for f in fixtures[:10]:
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        goals = f["goals"]
        msg += f"{home} {goals['home']} - {goals['away']} {away}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 *Top Leagues*\n\n"
        "🇬🇧 Premier League\n"
        "🇪🇸 La Liga\n"
        "🇮🇹 Serie A\n"
        "🇩🇪 Bundesliga\n"
        "🇫🇷 Ligue 1\n\n"
        "➡️ Type league name to continue",
        parse_mode="Markdown"
    )

async def standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Standings feature coming next update ✅")

async def my_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ *Choose Country*\n\n"
        "England\nSpain\nItaly\nGermany\nFrance\n\n"
        "➡️ Send country name",
        parse_mode="Markdown"
    )

# ================= AI =================
async def ai_reply(user_text: str):
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful football assistant."},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    data = r.json()

    try:
        return data["choices"][0]["message"]["content"]
    except:
        return "⚠️ AI is temporarily unavailable."

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "⚽ Live Scores":
        await live_scores(update, context)
    elif text == "🏆 Leagues":
        await leagues(update, context)
    elif text == "📊 Standings":
        await standings(update, context)
    elif text == "⭐ My Team":
        await my_team(update, context)
    elif text == "ℹ️ Help":
        await update.message.reply_text("Use buttons below to explore features 👇")
    elif text == "🤖 AI Chat":
        await update.message.reply_text("🤖 Ask me anything:")
    else:
        # 🔥 ANY OTHER TEXT → AI AUTO REPLY
        reply = await ai_reply(text)
        await update.message.reply_text(reply)

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
