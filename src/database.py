from supabase import create_client
import os
from datetime import datetime, timedelta
import pytz
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        self.client = create_client(url, key)
        self.timezone = pytz.timezone("Europe/Warsaw")

    def is_user_banned(self, user_id: int) -> bool:
        """Check if a user is currently banned."""
        try:
            response = (
                self.client.table("bans")
                .select("*")
                .eq("user_id", user_id)
                .lt("unban_date", datetime.now(self.timezone).isoformat())
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking ban status: {e}")
            return False

    def create_goal(self, user_id: int, user_name: str, target_visits: int) -> bool:
        """Create a new goal for the user."""
        try:
            # Check if user has an active goal
            active_goal = self.get_active_goal(user_id)
            if active_goal:
                return False

            # Calculate end date (next Saturday 23:50)
            now = datetime.now(self.timezone)
            days_until_saturday = (5 - now.weekday()) % 7  # 5 is Saturday
            if days_until_saturday == 0 and now.hour >= 23 and now.minute >= 50:
                days_until_saturday = 7
            end_date = now + timedelta(days=days_until_saturday)
            end_date = end_date.replace(hour=23, minute=50, second=0, microsecond=0)

            data = {
                "user_id": user_id,
                "user_name": user_name,
                "target_visits": target_visits,
                "current_visits": 0,
                "created_at": now.isoformat(),
                "end_date": end_date.isoformat(),
                "status": "active",
            }

            self.client.table("goals").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return False

    def get_active_goal(self, user_id: int):
        """Get user's active goal if exists."""
        try:
            response = (
                self.client.table("goals")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting active goal: {e}")
            return None

    def increment_visits(self, user_id: int) -> bool:
        """Increment visit count for user's active goal."""
        try:
            goal = self.get_active_goal(user_id)
            if not goal:
                return False

            self.client.table("goals").update(
                {"current_visits": goal["current_visits"] + 1}
            ).eq("id", goal["id"]).execute()
            return True
        except Exception as e:
            logger.error(f"Error incrementing visits: {e}")
            return False

    def ban_user(self, user_id: int, user_name: str, goal_id: int) -> bool:
        """Ban a user for failing their goal."""
        try:
            now = datetime.now(self.timezone)
            unban_date = now + timedelta(days=30)

            # Update goal status
            self.client.table("goals").update({"status": "failed"}).eq(
                "id", goal_id
            ).execute()

            # Create ban record
            ban_data = {
                "user_id": user_id,
                "user_name": user_name,
                "goal_id": goal_id,
                "ban_date": now.isoformat(),
                "unban_date": unban_date.isoformat(),
            }
            self.client.table("bans").insert(ban_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False

    def check_goals(self) -> list:
        """Check all active goals that have ended and return failed ones."""
        try:
            now = datetime.now(self.timezone)
            response = (
                self.client.table("goals")
                .select("*")
                .eq("status", "active")
                .lt("end_date", now.isoformat())
                .execute()
            )

            failed_goals = []
            for goal in response.data:
                if goal["current_visits"] < goal["target_visits"]:
                    failed_goals.append(goal)
                    # Update goal status
                    self.client.table("goals").update({"status": "failed"}).eq(
                        "id", goal["id"]
                    ).execute()
                else:
                    # Mark as completed
                    self.client.table("goals").update({"status": "completed"}).eq(
                        "id", goal["id"]
                    ).execute()

            return failed_goals
        except Exception as e:
            logger.error(f"Error checking goals: {e}")
            return []

    def get_message_history(
        self, user_id: int, max_messages: int = 20, max_age_hours: int = 72
    ) -> List[Dict[str, Any]]:
        """Get message history for a user with pruning rules applied."""
        try:
            cutoff_time = datetime.now(self.timezone) - timedelta(hours=max_age_hours)

            response = (
                self.client.table("messages")
                .select("role", "content", "created_at")
                .eq("user_id", user_id)
                .gte("created_at", cutoff_time.isoformat())
                .order("created_at", desc=True)
                .limit(max_messages)
                .execute()
            )

            # Convert to list and reverse to get chronological order
            messages = list(reversed(response.data))

            # Apply character limit (8000)
            total_chars = 0
            pruned_messages = []

            for msg in messages:
                msg_chars = len(msg["content"])
                if total_chars + msg_chars > 8000:
                    break
                total_chars += msg_chars
                pruned_messages.append(msg)

            return pruned_messages

        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []

    def add_message(self, user_id: int, content: str, role: str = "user") -> bool:
        """Add a new message to the history."""
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "role": role,
            }

            self.client.table("messages").insert(data).execute()
            return True

        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    def clear_old_messages(self, hours: int = 72) -> bool:
        """Clear messages older than specified hours."""
        try:
            cutoff_time = datetime.now(self.timezone) - timedelta(hours=hours)

            self.client.table("messages").delete().lt(
                "created_at", cutoff_time.isoformat()
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error clearing old messages: {e}")
            return False
