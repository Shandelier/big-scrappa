import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
import gzip
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from req import login, get_members_in_clubs
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket


# Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "hostname": socket.gethostname(),
            }
            self.wfile.write(json.dumps(health_status).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_health_check_server():
    """Run health check server on port 8080"""
    server = HTTPServer(("", 8080), HealthCheckHandler)
    logger.info("Started health check server on port 8080")
    server.serve_forever()


# Configure logging
def setup_logging():
    """Configure logging to both file and console with rotation"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Create formatter for cloud-friendly structured logging
    class CloudFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "severity": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "hostname": socket.gethostname(),
            }
            if record.exc_info:
                log_entry["error"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)

    # Setup file handler with rotation (10MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        "logs/scraper.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(CloudFormatter())

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CloudFormatter())

    # Get logger
    logger = logging.getLogger("WellFitnessScraper")
    logger.setLevel(logging.INFO)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()


def gather_data(max_retries=3, initial_delay=60):
    """Gather data using session-based authentication with retry mechanism"""
    try:
        # Load environment variables
        load_dotenv()
        username = os.getenv("WELLFITNESS_USERNAME")
        password = os.getenv("WELLFITNESS_PASSWORD")

        if not username or not password:
            logger.error("Missing credentials in environment variables")
            raise Exception("Missing credentials in environment variables")

        # Retry mechanism with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Attempting to gather data (attempt {attempt + 1}/{max_retries})"
                )
                # Create a new session and login
                session = login(username, password)
                logger.info("Successfully logged in")

                # Get data using the authenticated session
                response_text = get_members_in_clubs(session)
                data = json.loads(response_text)
                logger.info(
                    f"Successfully retrieved data for {len(data['UsersInClubList'])} clubs"
                )
                return data
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = initial_delay * (2**attempt)
                    logger.warning(
                        f"Login attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    raise Exception(
                        f"Failed to gather data after {max_retries} attempts: {e}"
                    )
    except Exception as e:
        logger.error(f"Error gathering data: {str(e)}")
        return None


def process_data(data):
    """Process the gathered data"""
    logger.info("Processing data...")
    try:
        # Create DataFrame from the response
        df = pd.DataFrame(data["UsersInClubList"])

        # Handle static data (clubs info)
        clubs_df = df[["ClubName", "ClubAddress"]].copy()
        clubs_df["club_id"] = clubs_df.index
        logger.info(f"Processed information for {len(clubs_df)} clubs")

        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create stats data
        stats_data = {"timestamp": timestamp}
        for _, row in df.iterrows():
            club_name = row["ClubName"].replace(" ", "_").replace(",", "")
            stats_data[club_name] = row["UsersCountCurrentlyInClub"]

        stats_df = pd.DataFrame([stats_data])
        logger.info("Successfully processed data")
        return clubs_df, stats_df
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise


def save_to_csv(clubs_df, stats_df, clubs_file="clubs.csv", stats_file="stats.csv"):
    """Save processed data to CSV files"""
    try:
        # Save clubs data if file doesn't exist
        if not os.path.isfile(clubs_file):
            clubs_df.to_csv(clubs_file, index=False)
            logger.info(f"Created new clubs file: {clubs_file}")

        # Save stats data
        if not os.path.isfile(stats_file):
            stats_df.to_csv(stats_file, index=False)
            logger.info(f"Created new stats file: {stats_file}")
        else:
            stats_df.to_csv(stats_file, mode="a", header=False, index=False)
            logger.info(f"Appended data to stats file: {stats_file}")
    except Exception as e:
        logger.error(f"Error saving CSV files: {str(e)}")
        raise


def save_raw_response(response_data, filename="raw_responses.jsonl.gz"):
    """Save raw JSON response with timestamp"""
    try:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": response_data,
        }

        mode = "ab" if os.path.exists(filename) else "wb"
        with gzip.open(filename, mode) as f:
            f.write((json.dumps(entry) + "\n").encode("utf-8"))
        logger.info(f"Saved raw response to {filename}")
    except Exception as e:
        logger.error(f"Error saving raw response: {str(e)}")
        raise


def backup_raw_responses(source_file="raw_responses.jsonl.gz"):
    """Create a daily backup of raw responses"""
    if os.path.exists(source_file):
        try:
            backup_filename = f"backup_raw_{datetime.now().strftime('%Y%m%d')}.jsonl.gz"
            with gzip.open(source_file, "rb") as f_in:
                with gzip.open(backup_filename, "wb") as f_out:
                    f_out.write(f_in.read())
            with gzip.open(source_file, "wb") as f:
                pass  # Truncate file
            logger.info(f"Created backup: {backup_filename}")
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise


def delete_old_backups(days=7):
    """Delete backup files older than specified days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        for file in os.listdir("."):
            if file.startswith("backup_raw_") and file.endswith(".jsonl.gz"):
                try:
                    file_date = datetime.strptime(file[11:19], "%Y%m%d")
                    if file_date < cutoff_date:
                        os.remove(file)
                        deleted_count += 1
                except (ValueError, OSError) as e:
                    logger.error(f"Error processing backup file {file}: {str(e)}")
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old backup files")
    except Exception as e:
        logger.error(f"Error during backup cleanup: {str(e)}")
        raise


# Main function to run the scraper
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Starting WellFitness Scraper")

    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_check_server, daemon=True)
    health_thread.start()

    # Get environment variables with defaults
    SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "600"))  # 10 minutes default
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

    last_backup_date = None

    # Log startup configuration
    logger.info(
        "Scraper configuration",
        extra={
            "scrape_interval": SCRAPE_INTERVAL,
            "backup_retention_days": BACKUP_RETENTION_DAYS,
            "data_directory": os.getcwd(),
        },
    )

    while True:
        try:
            current_date = datetime.now().date()

            # Check if we need to do daily backup
            if last_backup_date != current_date:
                logger.info("Performing daily backup tasks")
                backup_raw_responses()
                delete_old_backups(days=BACKUP_RETENTION_DAYS)
                last_backup_date = current_date

            data = gather_data()
            if data:
                save_raw_response(data)
                clubs_df, stats_df = process_data(data)
                save_to_csv(clubs_df, stats_df)
                logger.info("Successfully completed data collection cycle")
            else:
                logger.warning("No data collected in this cycle")

            logger.info("Waiting for next collection cycle...")
            time.sleep(SCRAPE_INTERVAL)

        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
            logger.info("Waiting before retry...")
            time.sleep(SCRAPE_INTERVAL)
