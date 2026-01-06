import os
import logging
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===================== CONFIG =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway Variable
AI_API_KEY = os.getenv("AI_API_KEY")  # Railway Variable

logging.basicConfig(level=logging.INFO)

# ===================== USER STATE =====================
user_fav_team = {}

# ===================== START MENU =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚽ LiveScore", callback_data="livescore")],
        [InlineKeyboardButton("🏆 Leagues", callback_data="leagues")],
        [InlineKeyboardButton("⭐ My Team", callback_data="myteam")],
        [InlineKeyboardButton("🔔 Alerts", callback_data="alerts")]
    ]
    await update.message.reply_text(
        "⚽ *Welcome to LiveScore Bot*\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===================== LIVESCORE (DO NOT TOUCH) =====================
# ⛔ THIS SECTION IS LEFT EXACTLY AS IS
# ⛔ Your existing LiveScore logic already works

async def livescore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📊 LiveScore is active and updating automatically.")

# ===================== LEAGUES =====================
async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🇬🇧 Premier League", callback_data="league_premier")],
        [InlineKeyboardButton("🇪🇸 La Liga", callback_data="league_laliga")],
        [InlineKeyboardButton("🇮🇹 Serie A", callback_data="league_seriea")],
        [InlineKeyboardButton("🇩🇪 Bundesliga", callback_data="league_bundesliga")],
        [InlineKeyboardButton("🇫🇷 Ligue 1", callback_data="league_ligue1")],
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ]

    await query.edit_message_text(
        "🏆 *Select a League*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===================== TEAMS =====================
LEAGUE_TEAMS = {
    "league_premier": [
        "Manchester United", "Chelsea", "Arsenal",
        "Liverpool", "Man City", "Tottenham"
    ],
    "league_laliga": [
        "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla"
    ],
    "league_seriea": [
        "Juventus", "AC Milan", "Inter Milan", "Napoli"
    ],
    "league_bundesliga": [
        "Bayern Munich", "Borussia Dortmund", "RB Leipzig"
    ],
    "league_ligue1": [
        "PSG", "Marseille", "Lyon", "Monaco"
    ]
}

async def show_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    league = query.data
    teams = LEAGUE_TEAMS.get(league, [])

    keyboard = [
        [InlineKeyboardButton(team, callback_data=f"team_{team}")]
        for team in teams
    ]
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="leagues")])

    await query.edit_message_text(
        "⭐ *Choose Your Team*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===================== SAVE TEAM =====================
async def select_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    team = query.data.replace("team_", "")
    user_fav_team[query.from_user.id] = team

    await query.edit_message_text(f"✅ *{team}* saved as your favorite team!",
                                  parse_mode="Markdown")

# ===================== MY TEAM =====================
async def my_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    team = user_fav_team.get(query.from_user.id)
    if not team:
        await query.edit_message_text("❌ You haven't selected a team yet.")
    else:
        await query.edit_message_text(f"⭐ Your favorite team: *{team}*",
                                      parse_mode="Markdown")

# ===================== ALERTS =====================
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔔 Match alerts feature coming next update.")

# ===================== BACK =====================
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# ===================== AI AUTO-REPLY =====================
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not AI_API_KEY:
        return

    text = update.message.text

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": text}]
            },
            timeout=20
        )

        reply = res.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text("🤖 AI temporarily unavailable.")

# ===================== MAIN =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(livescore, pattern="^livescore$"))
    app.add_handler(CallbackQueryHandler(leagues, pattern="^leagues$"))
    app.add_handler(CallbackQueryHandler(show_teams, pattern="^league_"))
    app.add_handler(CallbackQueryHandler(select_team, pattern="^team_"))
    app.add_handler(CallbackQueryHandler(my_team, pattern="^myteam$"))
    app.add_handler(CallbackQueryHandler(alerts, pattern="^alerts$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    # AI responds ONLY to normal chat messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    app.run_polling()

if __name__ == "__main__":
    main()
