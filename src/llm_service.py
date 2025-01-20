import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class LLMService:
    def __init__(self):
        # Set safety settings to allow all content
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self.model = genai.GenerativeModel(
            "gemini-2.0-flash-exp", safety_settings=safety_settings
        )
        self.chat = self.model.start_chat(history=[])

    async def get_response(
        self, message: str, user_name: str, has_active_goal: bool = False
    ) -> str:
        """Get a response for a normal message."""
        try:
            prompt = f"""You are a gym bro chatbot talking to {user_name}. 
            Be motivational but also funny and use gym bro slang.
            {'The user has an active gym goal.' if has_active_goal else 'The user does not have an active gym goal yet.'}
            
            User message: {message}
            
            Respond in a motivational gym bro style, keep it short and fun. Use emojis."""

            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 1.5},
            )

            return response.text

        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return "Sorry bro, my protein shake must've gone to my head! 🥤 Try again later! 💪"

    async def get_daily_motivation(
        self,
        user_name: str,
        has_active_goal: bool = False,
        current_visits: int = 0,
        target_visits: int = 0,
    ) -> str:
        """Get a daily motivational message."""
        try:
            goal_context = ""
            if has_active_goal:
                goal_context = f"They have completed {current_visits}/{target_visits} gym visits this week."

            prompt = f"""You are a gym bro chatbot generating a daily motivational message for {user_name}.
            {goal_context}
            
            Generate a short, motivational gym bro style message that will make them want to hit the gym today.
            Be creative, funny, and use gym bro slang and emojis.
            Keep it under 100 characters if possible."""

            response = self.model.generate_content(
                prompt, generation_config={"temperature": 1.5}
            )

            return response.text

        except Exception as e:
            logger.error(f"Error getting daily motivation: {e}")
            return "Rise and grind! Time to show those weights who's boss! 💪😤"
