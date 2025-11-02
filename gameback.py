import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineQueryResultGame
from telegram import InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.ext import ContextTypes, InlineQueryHandler

# --- CONFIGURATION (FINALIZED WITH YOUR VALUES) ---
# 1. Your API Token
BOT_TOKEN = "8574405914:AAHkq1xhlQZvf3dAZ36QIzK2PmSHCQ_ZTIA"
# 2. Your Game Short Name
GAME_SHORT_NAME = "ZathuraGame"
# 3. Your hosted game URL from Vercel
HOSTED_GAME_URL = "https://zathuragame1.vercel.app/game.html"
# 4. Webhook URL is set via environment variable by Render
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
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="🎮 Play Zathura Flyer",
            game=GAME_SHORT_NAME,
        )
    )
    await update.message.reply_text(
        "Welcome to the Zathura Flyer Game! Click the button below to start flying. Good luck!",
        reply_markup=keyboard,
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the callback when the user presses the inline button to start the game."""
    query = update.callback_query
    
    if query.game_short_name == GAME_SHORT_NAME:
        await query.answer(url=HOSTED_GAME_URL)
    else:
        await query.answer()

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline queries to suggest the game."""
    query = update.inline_query.query
    results = [
        InlineQueryResultGame(
            id="1", 
            game_short_name=GAME_SHORT_NAME,
        )
    ]
    
    await update.inline_query.answer(results, cache_time=5)

async def set_game_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the high score submission from the game (Telegram API handles the update)."""
    if update.callback_query and update.callback_query.game_short_name == GAME_SHORT_NAME:
        query = update.callback_query
        # Answer the query with the game URL to launch it
        await query.answer(url=HOSTED_GAME_URL)
    elif update.callback_query:
        # If it's a non-game button, just acknowledge the press
        await update.callback_query.answer()

def run_bot() -> None:
    """Initializes and runs the bot application."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Cannot run the bot.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # 1. Command handler for /start
    application.add_handler(CommandHandler("start", start_command))
    
    # 2. Callback handler for the inline game button press
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^' + GAME_SHORT_NAME + '$'))
    
    # 3. Inline Query Handler
    application.add_handler(InlineQueryHandler(inline_query_handler))
    
    # 4. Fallback callback handler for score updates
    application.add_handler(CallbackQueryHandler(set_game_score))

    # --- DEPLOYMENT MODE (WEBHOOK) ---
    if WEBHOOK_URL:
        logger.info(f"Starting bot with Webhook at {WEBHOOK_URL} on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,  # Use the token as a unique path
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            secret_token=BOT_TOKEN 
        )
    # --- LOCAL TESTING MODE (POLLING) ---
    else:
        logger.warning("WEBHOOK_URL not set. Running in local polling mode.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

# This function is the entry point Gunicorn is explicitly configured to call in the Procfile (gameback:main)
def main():
    """Main entry point for Gunicorn."""
    run_bot()

if __name__ == "__main__":
    # If run locally (e.g., python gameback.py), it calls the run_bot function
    run_bot()
