import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Add these lines to disable httpx and apscheduler logging:
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.full_name}) started the bot")
    await update.message.reply_text("Do you even lift bro? 💪")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user = update.effective_user
    logger.info(f"Message from {user.id} ({user.full_name}): {update.message.text}")
    await update.message.reply_text("Do you even lift bro? 💪")


def main() -> None:
    """Start the bot."""
    # Load environment variables
    load_dotenv()

    # Get the token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No token provided!")
        return

    # Create the Application and pass it your bot's token
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
