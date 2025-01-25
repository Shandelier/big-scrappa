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
from datetime import datetime, time, timedelta
from database import Database
from supabase import create_client, Client
from llm_service import LLMService
import re
import random

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Environment configuration
ENV = os.getenv("ENVIRONMENT", "development")  # Default to development if not set
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
logger.info(f"Starting bot in {ENV} environment (Debug: {DEBUG_MODE})")

# Get the appropriate token based on environment
if ENV == "production":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
else:
    token = os.getenv("TELEGRAM_BOT_TOKEN_DEV")

if not token:
    logger.error(f"No token provided for {ENV} environment!")
    raise ValueError(
        f"TELEGRAM_BOT_TOKEN{'_DEV' if ENV == 'development' else ''} not found in environment variables"
    )

# Initialize services
stats = GymStats(processed_dir="processed")
db = Database()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
llm = LLMService()

# Conversation states
VISITS = range(1)

# Define the times for scheduled jobs
WEEKLY_CHECK_TIME = time(hour=23, minute=50)  # Saturday 23:50
DAILY_MOTIVATION_TIME = time(hour=17, minute=10)  # Every day at 17:10
DAILY_TIP_START = time(hour=12, minute=0)  # Tips start time
DAILY_TIP_END = time(hour=18, minute=0)  # Tips end time

# Constants for message history
IMAGE_COMMAND_PATTERN = r"^/(status|plot|graph|chart|visualize|latestdata)"

# Create the Application
application = Application.builder().token(token).build()


async def send_ban_message(update: Update) -> None:
    """Send a standard ban message to the user."""
    await update.message.reply_text(
        "You're currently banned for failing your gym goal. 😔\n"
        "Come back when you're ready to commit to your fitness journey! 💪"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if db.is_user_banned(update.effective_user.id):
        await send_ban_message(update)
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
        await send_ban_message(update)
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
        await send_ban_message(update)
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
        await send_ban_message(update)
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when the command /help or /h is issued."""
    if db.is_user_banned(update.effective_user.id):
        await send_ban_message(update)
        return

    user = update.effective_user
    logger.info(f"User {user.id} ({user.full_name}) requested help")

    await update.message.reply_text(
        "Do you even lift bro? 💪\n\n"
        "Available commands:\n"
        "/status [days] - Check current gym stats (optionally specify number of days)\n"
        "/goal - Set your weekly gym goal\n"
        "/checkgoal - Check your current goal progress\n"
        "/latestdata - Get the most recent gym data\n"
        "/help or /h - Show this help message"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    if db.is_user_banned(update.effective_user.id):
        await send_ban_message(update)
        return

    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Message from {user.id} ({user.full_name}): {message_text}")

    # Skip storing image commands
    if re.match(IMAGE_COMMAND_PATTERN, message_text, re.IGNORECASE):
        # Handle image command normally
        await update.message.reply_text(
            "Sorry bro, that's an image command! I'll process it separately! 🖼️"
        )
        return

    # Get user's goal status
    active_goal = db.get_active_goal(user.id)

    # Store user's message
    db.add_message(user.id, message_text, role="user")

    # Get message history
    history = db.get_message_history(user.id)

    # Get LLM response with history
    response = await llm.get_response(
        message=message_text,
        user_name=user.full_name,
        has_active_goal=bool(active_goal),
        history=history,
    )

    # Store bot's response
    db.add_message(user.id, response, role="assistant")

    # Send response
    await update.message.reply_text(response)


async def send_daily_motivation(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily motivational messages to all users."""
    try:
        # Get all users who have interacted with the bot (from goals table)
        response = supabase.table("goals").select("user_id, user_name").execute()
        unique_users = {(goal["user_id"], goal["user_name"]) for goal in response.data}

        for user_id, user_name in unique_users:
            if not db.is_user_banned(user_id):
                try:
                    # Get user's current goal if any
                    active_goal = db.get_active_goal(user_id)

                    # Get motivational message
                    message = await llm.get_daily_motivation(
                        user_name=user_name,
                        has_active_goal=bool(active_goal),
                        current_visits=(
                            active_goal["current_visits"] if active_goal else 0
                        ),
                        target_visits=(
                            active_goal["target_visits"] if active_goal else 0
                        ),
                    )

                    # Send the message
                    await context.bot.send_message(chat_id=user_id, text=message)

                except Exception as e:
                    logger.error(f"Error sending motivation to user {user_id}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error in daily motivation job: {e}")


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
                f"Wro Ferio Gaj: {latest_record['Wrocław_Ferio_Gaj']}\n"
            )
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("No data found in Supabase.")
    except Exception as e:
        logger.error(f"Error downloading data from Supabase: {str(e)}")
        await update.message.reply_text(
            "Sorry, couldn't fetch the latest data right now 😔"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.message:
            await update.message.reply_text(
                "Sorry, something went wrong! Please try again later. 😔"
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")


async def send_daily_tip(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily gym tips to all users at random time."""
    try:
        # Get all users who have interacted with the bot
        response = supabase.table("goals").select("user_id, user_name").execute()
        unique_users = {(goal["user_id"], goal["user_name"]) for goal in response.data}

        for user_id, user_name in unique_users:
            if not db.is_user_banned(user_id):
                try:
                    # Get tip message
                    message = await llm.get_daily_tip(user_name=user_name)
                    await context.bot.send_message(chat_id=user_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending tip to user {user_id}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error in daily tip job: {e}")


def get_random_time(start: time, end: time) -> datetime:
    """Get a random time between start and end for today."""
    now = datetime.now()
    start_dt = datetime.combine(now.date(), start)
    end_dt = datetime.combine(now.date(), end)

    # If current time is past end time, schedule for tomorrow
    if now.time() > end:
        start_dt += timedelta(days=1)
        end_dt += timedelta(days=1)
    # If current time is before start time, use today
    elif now.time() < start:
        pass
    # If current time is between start and end, use remaining time today
    else:
        start_dt = now

    time_diff = (end_dt - start_dt).total_seconds()
    random_seconds = random.randint(0, int(time_diff))
    return start_dt + timedelta(seconds=random_seconds)


def main() -> None:
    """Start the bot."""
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
    application.add_handler(CommandHandler(["status", "s"], status))
    application.add_handler(CommandHandler(["checkgoal", "cg"], checkgoal))
    application.add_handler(CommandHandler(["help", "h"], help_command))
    application.add_handler(goal_handler)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Add error handler
    application.add_error_handler(error_handler)

    # Schedule jobs
    job_queue = application.job_queue

    # Weekly goal check (every Saturday at 23:50)
    job_queue.run_daily(
        check_failed_goals,
        time=WEEKLY_CHECK_TIME,
        days=(5,),  # 5 represents Saturday (0-6 = Monday-Sunday)
    )

    # Daily motivation (every day at 17:10)
    job_queue.run_daily(send_daily_motivation, time=DAILY_MOTIVATION_TIME)

    # Schedule first daily tip
    first_tip_time = get_random_time(DAILY_TIP_START, DAILY_TIP_END)
    job_queue.run_once(send_daily_tip, when=first_tip_time)

    # Add callback to schedule next day's tip after current one runs
    async def schedule_next_tip(context: ContextTypes.DEFAULT_TYPE) -> None:
        next_tip_time = get_random_time(DAILY_TIP_START, DAILY_TIP_END)
        context.job_queue.run_once(send_daily_tip, when=next_tip_time)
        logger.info(f"Scheduled next tip for: {next_tip_time}")

    job_queue.run_once(schedule_next_tip, when=first_tip_time)

    # Add a command handler for downloading the newest data
    application.add_handler(
        CommandHandler("latestdata", download_newest_data_from_supabase)
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
