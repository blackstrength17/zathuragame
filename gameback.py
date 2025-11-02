import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineQueryResultGame
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.ext import ContextTypes, InlineQueryHandler, MessageHandler, filters
from telegram.error import TelegramError

# --- CONFIGURATION (FINALIZED WITH YOUR VALUES) ---
# 1. Your API Token
BOT_TOKEN = "8574405914:AAHkq1xhlQZvf3dAZ36QIzK2PmSHCQ_ZTIA"
# 2. Your Game Short Name (Used for internal commands and buttons)
GAME_SHORT_NAME = "ZathuraGame"
# 3. Your Game TITLE (Used for the API fix attempt)
GAME_TITLE = "Flappy Zathura"
# 4. Your hosted game URL from Vercel
HOSTED_GAME_URL = "https://zathuragame1.vercel.app/game.html"
# 5. Webhook URL is set via environment variable by Render
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
# 6. Port required by the hosting service
PORT = int(os.environ.get("PORT", 8443))

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Instantiate the Application globally 
application = Application.builder().token(BOT_TOKEN).build()

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
        # This opens the game URL when the main "Play" button is pressed
        await query.answer(url=HOSTED_GAME_URL)
    else:
        # A general callback (e.g., if a retry button were a separate inline button)
        await query.answer()

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline queries to suggest the game."""
    if not update.inline_query:
        return
        
    results = [
        InlineQueryResultGame(
            id="1", 
            game_short_name=GAME_SHORT_NAME,
        )
    ]
    
    await update.inline_query.answer(results, cache_time=5)

async def set_game_url_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """TEMPORARY DEBUG COMMAND: Forces the game URL update via API call."""
    try:
        # Using the Game Title as the identifier for the API call (as a final fix attempt)
        success = await context.bot.set_game_short_name(
            game_short_name=GAME_TITLE, 
            url=HOSTED_GAME_URL
        )
        
        if success:
            message = f"✅ API SUCCESS: Game URL updated successfully using TITLE! URL: {HOSTED_GAME_URL}"
        else:
            message = "❌ API FAILURE: Telegram API returned False. Check BotFather settings."

    except TelegramError as e:
        message = f"❌ API ERROR: Telegram rejected the request. Reason: {e.message}"
        logger.error(f"Telegram API Error in /setgameurl: {e.message}")

    except Exception as e:
        message = f"❌ UNEXPECTED ERROR: Failed to run command. Reason: {e}"
        logger.error(f"Unexpected error in /setgameurl: {e}")

    await update.message.reply_text(message)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles any text that isn't a command, logging it to confirm server is working."""
    if update.message and update.message.text:
        await update.message.reply_text(f"Bot received: '{update.message.text}'. Commands must start with /")

async def set_game_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the high score submission from the game (Telegram API handles the update)."""
    # The setScore is sent from the HTML game's JavaScript (TelegramGameProxy.setScore)
    # The bot handles the resultant API update, but the score submission itself is client-side.
    if update.callback_query and update.callback_query.game_short_name == GAME_SHORT_NAME:
        await update.callback_query.answer(url=HOSTED_GAME_URL)
    elif update.callback_query:
        await update.callback_query.answer()

def run_app_setup(application: Application) -> None:
    """Configures all handlers for the application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("setgameurl", set_game_url_command))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^' + GAME_SHORT_NAME + '$'))
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(CallbackQueryHandler(set_game_score))

def main() -> None:
    """Runs the application with webhook or polling. Used by Gunicorn."""
    run_app_setup(application) 

    # --- DEPLOYMENT MODE (WEBHOOK) ---
    if WEBHOOK_URL:
        logger.info(f"Starting bot with Webhook at {WEBHOOK_URL} on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,  
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            secret_token=BOT_TOKEN 
        )
    # --- LOCAL TESTING MODE (POLLING) ---
    else:
        logger.warning("WEBHOOK_URL not set. Running in local polling mode.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
