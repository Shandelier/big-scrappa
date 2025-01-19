import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv
import os
from gym_stats import GymStats
from datetime import datetime, time
from database import Database
from supabase import create_client, Client

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Add these lines to disable httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
# Initialize GymStats and Database
stats = GymStats(processed_dir="processed")
db = Database()

# Conversation states
VISITS = range(1)

# Define the time for the weekly check (Saturday 23:50)
WEEKLY_CHECK_TIME = time(hour=23, minute=50)

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if db.is_user_banned(update.effective_user.id):
        await update.message.reply_text(
            "You're currently banned for failing your gym goal. 😔\n"
            "Come back when you're ready to commit to anything 💀"
        )
        return

    user = update.effective_user
    logger.info(f"User {user.id} ({user.full_name}) started the bot")
    await update.message.reply_text(
        "Do you even lift bro? 💀\n"
        "Use /status to check gym stats!\n"
        "Use /goal to set a weekly gym goal!"
    )


async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the goal setting process."""
    if db.is_user_banned(update.effective_user.id):
        await update.message.reply_text(
            "You're currently banned for failing your gym goal. 😔\n"
            "Come back when you're ready to commit to your fitness journey! 💪"
        )
        return ConversationHandler.END

    user = update.effective_user
    active_goal = db.get_active_goal(user.id)

    if active_goal:
        end_date = datetime.fromisoformat(active_goal["end_date"])
        await update.message.reply_text(
            f"You already have an active goal!\n"
            f"Target: {active_goal['target_visits']} visits\n"
            f"Current progress: {active_goal['current_visits']}/{active_goal['target_visits']}\n"
            f"End date: {end_date.strftime('%Y-%m-%d %H:%M')}"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's set a weekly gym goal! 🎯\n"
        "How many times will you go to the gym this week? (1-5)\n"
        "Choose wisely - if you fail, you'll be banned for a month! 😱"
    )
    return VISITS


async def set_visits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the number of visits response."""
    try:
        visits = int(update.message.text)
        if not 1 <= visits <= 5:
            await update.message.reply_text(
                "Please choose a number between 1 and 5! 🔢"
            )
            return VISITS

        user = update.effective_user
        if db.create_goal(user.id, user.full_name, visits):
            goal = db.get_active_goal(user.id)
            end_date = datetime.fromisoformat(goal["end_date"])
            await update.message.reply_text(
                f"Goal set! 🎯\n"
                f"You committed to {visits} gym visits this week.\n"
                f"Deadline: {end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Don't let me down, bro! 💪"
            )
        else:
            await update.message.reply_text(
                "Sorry, couldn't set your goal right now. Try again later! 😔"
            )
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number between 1 and 5! 🔢"
        )
        return VISITS

    return ConversationHandler.END


async def checkgoal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check current goal progress."""
    if db.is_user_banned(update.effective_user.id):
        await update.message.reply_text(
            "You're currently banned for failing your gym goal. 😔\n"
            "Come back when you're ready to commit to your fitness journey! 💪"
        )
        return

    user = update.effective_user
    goal = db.get_active_goal(user.id)

    if not goal:
        await update.message.reply_text(
            "You don't have an active goal! 🤔\n" "Use /goal to set one!"
        )
        return

    end_date = datetime.fromisoformat(goal["end_date"])
    await update.message.reply_text(
        f"Current Goal Progress 📊\n"
        f"Target: {goal['target_visits']} visits\n"
        f"Current progress: {goal['current_visits']}/{goal['target_visits']}\n"
        f"Deadline: {end_date.strftime('%Y-%m-%d %H:%M')}\n"
        f"Keep pushing! 💪"
    )


async def check_failed_goals(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for failed goals and ban users."""
    failed_goals = db.check_goals()
    for goal in failed_goals:
        # Ban the user
        if db.ban_user(goal["user_id"], goal["user_name"], goal["id"]):
            try:
                await context.bot.send_message(
                    chat_id=goal["user_id"],
                    text=(
                        "You failed to reach your gym goal! 😔\n"
                        "As agreed, you're banned for 30 days.\n"
                        "Use this time to reflect on your commitment!\n"
                        "See you in a month, when you're ready to try again! 💪"
                    ),
                )
            except Exception as e:
                logger.error(
                    f"Error sending ban message to user {goal['user_id']}: {e}"
                )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send current gym statistics."""
    if db.is_user_banned(update.effective_user.id):
        await update.message.reply_text(
            "You're currently banned for failing your gym goal. 😔\n"
            "Come back when you're ready to commit to your fitness journey! 💪"
        )
        return

    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.full_name}) requested status")

        # Get the number of days from command arguments (default to 1 if not provided)
        days = 1
        if context.args:
            try:
                days = int(context.args[0])
                if days < 1:
                    await update.message.reply_text(
                        "Please provide a positive number of days!"
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    "Please provide a valid number of days!"
                )
                return

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

        DAYS_INTERVAL_RATIO_DICT = {
            1: "20min",
            2: "30min",
            3: "40min",
            4: "60min",
        }

        interval = DAYS_INTERVAL_RATIO_DICT.get(days, "60min")

        # Create and send the plot with specified number of days
        logger.info(f"Generating time series plot for {days} days")
        plot_buf = stats.create_time_series_plot(hours=24 * days, interval=interval)

        # Send the plot
        await update.message.reply_photo(
            photo=plot_buf,
            caption=f"Members count over the last {days} {'day' if days == 1 else 'days'} 📊",
        )

    except Exception as e:
        logger.error(f"Error sending status: {e}")
        await update.message.reply_text("Sorry, couldn't fetch gym stats right now 😔")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    if db.is_user_banned(update.effective_user.id):
        return  # Silently ignore messages from banned users

    user = update.effective_user
    logger.info(f"Message from {user.id} ({user.full_name}): {update.message.text}")
    await update.message.reply_text(
        "Do you even lift bro? 💪\n"
        "Use /status to check gym stats!\n"
        "Use /goal to set a weekly gym goal!"
    )


async def download_newest_data_from_supabase(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Download the newest data from Supabase and send it to the user."""
    try:
        # Query the newest data
        response = (
            supabase.table("gym_stats")
            .select("*")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        data = response.data
        if data:
            latest_record = data[0]
            message = (
                f"Latest Gym Data 📊\n"
                f"Timestamp: {latest_record['timestamp']}\n"
                f"Location: {latest_record['location']}\n"
                f"Users Count: {latest_record['users_count']}"
            )
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("No data found in Supabase.")
    except Exception as e:
        logger.error(f"Error downloading data from Supabase: {str(e)}")
        await update.message.reply_text(
            "Sorry, couldn't fetch the latest data right now 😔"
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

    # Add conversation handler for goal setting
    goal_handler = ConversationHandler(
        entry_points=[CommandHandler("goal", goal)],
        states={
            VISITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_visits)],
        },
        fallbacks=[],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("checkgoal", checkgoal))
    application.add_handler(goal_handler)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Schedule the weekly goal check (every Saturday at 23:50)
    job_queue = application.job_queue
    job_queue.run_daily(
        check_failed_goals,
        time=WEEKLY_CHECK_TIME,
        days=(5,),  # 5 represents Saturday (0-6 = Monday-Sunday)
    )

    # Add a command handler for downloading the newest data
    application.add_handler(
        CommandHandler("latestdata", download_newest_data_from_supabase)
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
