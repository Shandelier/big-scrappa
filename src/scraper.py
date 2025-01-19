import requests
import pandas as pd
import time
from datetime import datetime
import os
import json
import logging
from dotenv import load_dotenv
from req import login, get_members_in_clubs
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from supabase import create_client, Client


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


# Configure basic logging
logger = logging.getLogger("WellFitnessScraper")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
logger.addHandler(console_handler)


def validate_member_count(count):
    """Validate that the member count is a reasonable number"""
    try:
        count = int(count)
        # Gym capacity is unlikely to exceed 1000, and negative numbers are invalid
        if count < 0 or count > 1000:
            logger.warning(f"Suspicious member count: {count}")
            return False
        return True
    except (ValueError, TypeError):
        logger.error(f"Invalid member count value: {count}")
        return False


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

                # Get data using the authenticated session
                response_text = get_members_in_clubs(session)
                data = json.loads(response_text)

                # Validate response structure
                if not isinstance(data, dict) or "UsersInClubList" not in data:
                    raise ValueError("Invalid response format from API")

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
    """Process the gathered data into format for gym_stats table"""
    try:
        # Create DataFrame from the response
        df = pd.DataFrame(data["UsersInClubList"])

        # Validate that we have the expected columns
        required_columns = ["ClubName", "UsersCountCurrentlyInClub"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Expected: {required_columns}")

        # Create timestamp in the format: "2025-01-19 18:57:50.260122+00"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f+00")

        # Find Wrocław Ferio Gaj specifically
        gaj_data = df[df["ClubName"].str.contains("Ferio Gaj", case=False, na=False)]

        if len(gaj_data) == 0:
            raise ValueError("Could not find Wrocław Ferio Gaj in the data")
        if len(gaj_data) > 1:
            raise ValueError("Multiple matches found for Wrocław Ferio Gaj")

        # Convert NumPy int64 to regular Python int
        member_count = int(gaj_data.iloc[0]["UsersCountCurrentlyInClub"])

        # Validate member count
        if not validate_member_count(member_count):
            raise ValueError(f"Invalid member count: {member_count}")

        # Create stats data
        stats_data = {
            "timestamp": timestamp,
            "Wrocław_Ferio_Gaj": member_count,
        }

        logger.info(f"Processed data: {stats_data}")
        return stats_data
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise


def save_to_supabase(stats_data, raw_data):
    """Save both processed stats and raw data to Supabase"""
    try:
        # Validate data before saving
        if not isinstance(stats_data, dict):
            raise ValueError("stats_data must be a dictionary")

        if "timestamp" not in stats_data or "Wrocław_Ferio_Gaj" not in stats_data:
            raise ValueError("Missing required fields in stats_data")

        if not isinstance(raw_data, dict):
            raise ValueError("raw_data must be a dictionary")

        # Save processed stats
        supabase.table("gym_stats").insert(stats_data).execute()
        logger.info("Saved processed stats to Supabase")

        # Save raw response
        raw_entry = {"timestamp": stats_data["timestamp"], "response": raw_data}
        supabase.table("raw_responses").insert(raw_entry).execute()
        logger.info("Saved raw response to Supabase")
    except Exception as e:
        logger.error(f"Error saving to Supabase: {str(e)}")
        raise


# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Main function to run the scraper
if __name__ == "__main__":
    logger.info("Starting WellFitness Scraper")

    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_check_server, daemon=True)
    health_thread.start()

    # Get environment variables with defaults
    SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "600"))  # 10 minutes default

    # Log startup configuration
    logger.info(f"Starting scraper with interval: {SCRAPE_INTERVAL} seconds")

    while True:
        try:
            data = gather_data()
            if data:
                stats_data = process_data(data)
                save_to_supabase(stats_data, data)
            else:
                logger.warning("No data collected in this cycle")

            time.sleep(SCRAPE_INTERVAL)

        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
            logger.info("Waiting before retry...")
            time.sleep(SCRAPE_INTERVAL)
