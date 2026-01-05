# live_score_bot.py
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== CONFIG =====
TELEGRAM_BOT_TOKEN = "8397940146:AAGGI53SIp5f-SulUzBT4mueAfkJLc3EkWI"  # Replace with your BotFather token
API_KEY = "13c68bc4d00c421d41dae0288e21b60a"
API_URL = "https://v3.football.api-sports.io/fixtures?live=all"
HEADERS = {"x-apisports-key": API_KEY}
FETCH_INTERVAL = 60  # seconds

# ===== FUNCTIONS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Live Matches", callback_data='live')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to LiveScore Bot!", reply_markup=reply_markup)

def fetch_live_matches():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        data = response.json()
        matches = data.get("response", [])
        if not matches:
            return "No live matches right now."
        message = "⚽ Live Matches:\n\n"
        for match in matches:
            fixture = match["fixture"]
            teams = match["teams"]
            goals = match["goals"]
            message += f"{teams['home']['name']} {goals['home']} - {goals['away']} {teams['away']['name']}\n"
            message += f"Time: {fixture['status']['elapsed']}\'\n\n"
        return message
    except Exception as e:
        return f"Error fetching live scores: {e}"

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'live':
        text = fetch_live_matches()
        await query.edit_message_text(text=text, reply_markup=query.message.reply_markup)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()  # <- run_polling handles the event loop internally

if __name__ == "__main__":
    main()
