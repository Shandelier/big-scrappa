import asyncio
import os
from datetime import datetime
import sys
from pathlib import Path
import time
import random

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from llm_service import LLMService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Rate limiting settings
REQUESTS_PER_MINUTE = 9
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE  # seconds

# Test data
TEST_USERS = [
    {"name": "John", "has_goal": True, "visits": 4, "target": 4},
    {"name": "Mike", "has_goal": False},
    {"name": "Sarah", "has_goal": True, "visits": 4, "target": 5},
    {"name": "Alex", "has_goal": True, "visits": 0, "target": 3},
    {"name": "Emma", "has_goal": False},
]

TEST_MESSAGES = [
    "I'm new to gym, where should I start?",
    "My muscles are sore, should I skip today?",
    "What's the best protein powder?",
    "I'm not seeing results after 2 months :(",
    "How often should I train each muscle group?",
    "Is it normal to feel intimidated at the gym?",
    "Should I do cardio before or after weights?",
    "How do I know if my form is correct?",
    "What should I eat before workout?",
    "How do I get motivated on lazy days?",
]


class PreviewGenerator:
    def __init__(self):
        self.llm = LLMService()
        self.last_request_time = 0
        self.results_file = None
        self.current_section = None

    async def rate_limit(self):
        """Ensure we don't exceed rate limits."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < DELAY_BETWEEN_REQUESTS:
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS - time_since_last)
        self.last_request_time = time.time()

    def start_results_file(self):
        """Initialize results file and write header."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/preview/results_{timestamp}.md"
        self.results_file = open(filename, "w", encoding="utf-8")

        header = f"""# LLM Preview Tests
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Model: gemini-2.0-flash-experimental

"""
        self.results_file.write(header)
        self.results_file.flush()
        print(f"Started generating preview results in: {filename}")

    def write_section(self, title: str, description: str = ""):
        """Write a new section header."""
        self.current_section = title
        self.results_file.write(f"\n## {title}\n{description}\n\n")
        self.results_file.flush()
        print(f"\nStarting section: {title}")

    def write_result(self, content: str):
        """Write a result and flush immediately."""
        self.results_file.write(content)
        self.results_file.flush()
        # Print a short preview
        preview = content.split("\n")[0][:100] + "..."
        print(f"Added result to {self.current_section}: {preview}")

    async def generate_daily_motivation_previews(self, count: int = 10):
        """Generate sample daily motivations."""
        self.write_section(
            "Daily Motivations", "Testing different scenarios (with/without goals)"
        )

        for i in range(count):
            user = TEST_USERS[i % len(TEST_USERS)]
            try:
                await self.rate_limit()
                response = await self.llm.get_daily_motivation(
                    user_name=user["name"],
                    has_active_goal=user["has_goal"],
                    current_visits=user.get("visits", 0),
                    target_visits=user.get("target", 0),
                )

                content = f"{i+1}. **Scenario**: {'With goal' if user['has_goal'] else 'No goal'}"
                if user["has_goal"]:
                    content += f" ({user['visits']}/{user['target']} visits)"
                content += f"\n   **User**: {user['name']}\n"
                content += f"   **Response**: {response}\n\n"

                self.write_result(content)

            except Exception as e:
                error_content = (
                    f"{i+1}. **ERROR**: {str(e)}\n   **User**: {user['name']}\n\n"
                )
                self.write_result(error_content)
                print(f"Error in daily motivation: {str(e)}")

    async def generate_daily_tip_previews(self, count: int = 10):
        """Generate sample daily tips."""
        self.write_section("Daily Tips", "Testing random topics from our list")

        used_topics = set()
        for i in range(count):
            user = TEST_USERS[i % len(TEST_USERS)]
            try:
                available_topics = [
                    t for t in self.llm.GYM_TOPICS if t not in used_topics
                ]
                if not available_topics:
                    used_topics.clear()
                    available_topics = self.llm.GYM_TOPICS

                topic = random.choice(available_topics)
                used_topics.add(topic)

                await self.rate_limit()
                response = await self.llm.get_daily_tip(
                    user_name=user["name"], topic=topic
                )

                content = f"{i+1}. **Topic**: {topic}\n"
                content += f"   **User**: {user['name']}\n"
                content += f"   **Response**: {response}\n\n"

                self.write_result(content)

            except Exception as e:
                error_content = f"{i+1}. **ERROR**: {str(e)}\n   **Topic**: {topic}\n   **User**: {user['name']}\n\n"
                self.write_result(error_content)
                print(f"Error in daily tip: {str(e)}")

    async def generate_conversation_previews(self, count: int = 10):
        """Generate sample conversations."""
        self.write_section(
            "Conversation Responses", "Testing various user questions/scenarios"
        )

        for i in range(count):
            message = TEST_MESSAGES[i % len(TEST_MESSAGES)]
            user = TEST_USERS[i % len(TEST_USERS)]
            try:
                await self.rate_limit()
                response = await self.llm.get_response(
                    message=message,
                    user_name=user["name"],
                    has_active_goal=user["has_goal"],
                )

                content = f"{i+1}. **User**: {user['name']} "
                content += f"({'With goal' if user['has_goal'] else 'No goal'})\n"
                content += f'   **Message**: "{message}"\n'
                content += f"   **Response**: {response}\n\n"

                self.write_result(content)

            except Exception as e:
                error_content = (
                    f"{i+1}. **ERROR**: {str(e)}\n"
                    f"   **User**: {user['name']}\n"
                    f'   **Message**: "{message}"\n\n'
                )
                self.write_result(error_content)
                print(f"Error in conversation: {str(e)}")

    def close(self):
        """Close the results file."""
        if self.results_file:
            self.results_file.close()
            print("\nFinished generating preview results!")


async def main():
    generator = PreviewGenerator()
    generator.start_results_file()

    try:
        # await generator.generate_daily_motivation_previews()
        await generator.generate_daily_tip_previews()
        # await generator.generate_conversation_previews()
    finally:
        generator.close()


if __name__ == "__main__":
    asyncio.run(main())
