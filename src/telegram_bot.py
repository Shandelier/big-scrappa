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
from gym_stats import GymStats
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Add these lines to disable httpx and apscheduler logging:
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize GymStats
stats = GymStats(data_dir="data", processed_dir="processed")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.full_name}) started the bot")
    await update.message.reply_text(
        "Do you even lift bro? 💀\nUse /status to check gym stats!"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send current gym statistics."""
    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.full_name}) requested status")

        # Get stats summary
        summary = stats.get_stats_summary()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create status message
        message = (
            f"🏋️‍♂️ Gym Status Report - {current_time}\n\n"
            f"Current members: {summary['current_members']} 👥\n"
            f"Maximum in last 7 days: {summary['max_7d']} 📈\n"
        )

        # Send text message first
        await update.message.reply_text(message)

        # Create and send the plot
        logger.info("Generating time series plot")
        plot_buf = stats.create_time_series_plot(hours=24, interval="20min", save=False)

        # Send the plot
        await update.message.reply_photo(
            photo=plot_buf, caption="Members count over the last 24 hours 📊"
        )

    except Exception as e:
        logger.error(f"Error sending status: {e}")
        await update.message.reply_text("Sorry, couldn't fetch gym stats right now 😔")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    user = update.effective_user
    logger.info(f"Message from {user.id} ({user.full_name}): {update.message.text}")
    await update.message.reply_text(
        "Do you even lift bro? 💪\nUse /status to check gym stats!"
    )


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
    application.add_handler(CommandHandler("status", status))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
