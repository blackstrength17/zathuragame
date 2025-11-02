import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# --- CONFIGURATION (MUST BE EDITED) ---
# 1. Replace with the API Token you got from BotFather
BOT_TOKEN = "8574405914:AAHkq1xhlQZvf3dAZ36QIzK2PmSHCQ_ZTIA"
# 2. Replace with the Game Short Name you registered with BotFather (e.g., "TelegramFlyer")
GAME_SHORT_NAME = "ZathuraGame"
# 3. Replace with the public HTTPS URL where you hosted 'game.html'
HOSTED_GAME_URL = "https://zathuragame1.vercel.app/game.html"
# 4. Webhook URL will be provided by your hosting service (e.g., Render/Heroku)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
# 5. Port required by the hosting service
PORT = int(os.environ.get("PORT", 8443))

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with a button that launches the game."""
    # Ensure the button's game short name matches the one registered with BotFather
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="🎮 Play Telegram Flyer",
            game=GAME_SHORT_NAME,
        )
    )
    await update.message.reply_text(
        "Welcome to the Telegram Flyer Game! Click the button below to start flying. Good luck!",
        reply_markup=keyboard,
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the callback when the user presses the inline button to start the game."""
    query = update.callback_query
    
    # We use answer with the URL to open the Web App (the HTML5 game).
    # The URL MUST be the HOSTED_GAME_URL you set up in BotFather.
    if query.game_short_name == GAME_SHORT_NAME:
        await query.answer(url=HOSTED_GAME_URL)
    else:
        # A general button callback, just answer the query
        await query.answer()

async def set_game_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the high score submission from the game (Telegram API handles the update)."""
    # This function primarily exists to catch and launch the game on button press.
    # The TelegramGameProxy.setScore call from the HTML game automatically updates
    # the score on the message in the chat via the Telegram API, so custom score
    # logic here is usually minimal unless you need a database.
    
    # Check if this is a callback for our registered game short name
    if update.callback_query and update.callback_query.game_short_name == GAME_SHORT_NAME:
        query = update.callback_query
        # Answer the query with the game URL to launch it
        await query.answer(url=HOSTED_GAME_URL)
    elif update.callback_query:
        # If it's a non-game button, just acknowledge the press
        await update.callback_query.answer()


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logger.error("BOT_TOKEN is not set. Please update the configuration and restart.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # 1. Command handler for /start
    application.add_handler(CommandHandler("start", start_command))
    
    # 2. Callback handler for the inline game button press
    # The pattern checks for a callback query that refers to our registered game short name
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^' + GAME_SHORT_NAME + '$'))
    
    # 3. Fallback callback handler for score updates (which also catches the button press)
    application.add_handler(CallbackQueryHandler(set_game_score))

    # --- DEPLOYMENT MODE (WEBHOOK) ---
    if WEBHOOK_URL:
        logger.info(f"Starting bot with Webhook at {WEBHOOK_URL} on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,  # Use the token as a unique path for Telegram to send updates
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            secret_token=BOT_TOKEN # Simple secret for verification
        )
    # --- LOCAL TESTING MODE (POLLING) ---
    else:
        logger.warning("WEBHOOK_URL not set. Running in local polling mode. The bot will stop when this script stops.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
