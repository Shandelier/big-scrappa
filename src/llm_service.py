import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Tuple
import asyncio
from google.api_core import retry
import random

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


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

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format message history into a string."""
        if not history:
            return ""

        formatted = "\nPrevious conversation:\n"
        for msg in history:
            role = "USER" if msg["role"] == "user" else "ASSISTANT"
            formatted += f"{role}: {msg['content']}\n"
        return formatted

    async def _generate_with_retry(self, prompt: str, temperature: float = 1.5) -> str:
        """Generate content with retry mechanism."""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": temperature},
                )
                return response.text
            except Exception as e:
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    logger.error(f"Final retry attempt failed: {e}")
                    raise  # Re-raise the last exception
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff

    async def get_response(
        self,
        message: str,
        user_name: str,
        has_active_goal: bool = False,
        history: List[Dict[str, Any]] = None,
    ) -> str:
        """Get a response for a normal message."""
        try:
            history_context = self._format_history(history) if history else ""

            prompt = f"""You are a gym bro chatbot talking to a user named{user_name}. 
            Be motivational but also funny and use gym bro slang.
            Respond in a motivational gym bro style, keep it short and fun. Use emojis.
            {'The user has an active gym goal.' if has_active_goal else 'The user does not have an active gym goal yet.'}
            {history_context}
            
            User message: {message}
            Your response:
            """

            if DEBUG_MODE:
                logger.info(f"LLM Prompt:\n{prompt}")

            response_text = await self._generate_with_retry(prompt)
            return response_text

        except Exception as e:
            logger.error(f"Error getting LLM response after all retries: {e}")
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

            if DEBUG_MODE:
                logger.info(f"LLM Prompt:\n{prompt}")

            response_text = await self._generate_with_retry(prompt)
            return response_text

        except Exception as e:
            logger.error(f"Error getting daily motivation after all retries: {e}")
            return "Rise and grind! Time to show those weights who's boss! 💪😤"

    # List of gym topics for daily tips
    GYM_TOPICS = [
        "best exercises for triceps",
        "best exercises for biceps",
        "best exercises for chest",
        "best exercises for back",
        "best exercises for shoulders",
        "best exercises for legs",
        "best exercises for abs",
        "how to properly warm up",
        "how much protein to eat",
        "best pre-workout snacks",
        "post-workout nutrition tips",
        "how to prevent injuries",
        "how to track progress",
        "rest between sets",
        "best time to exercise",
        "how to stay motivated",
        "common gym mistakes",
        "how to improve form",
        "breathing during exercises",
        "how to increase strength",
        "recovery tips",
        "sleep and muscle growth",
        "hydration tips",
        "supplements worth taking",
        "how to spot properly",
        "gym etiquette tips",
    ]

    async def get_daily_tip(
        self,
        user_name: str,
    ) -> str:
        """Get a daily gym tip message."""
        try:
            # Randomly select a topic
            topic = random.choice(self.GYM_TOPICS)

            prompt = f"""Yo! You're a gym bro who's been working out consistently for about a year, messaging your friend {user_name}.
            You just learned something cool about: {topic}

            Share this knowledge with your friend in an excited, casual way - like you just discovered this and can't wait to tell them!
            Use gym bro slang, but also show that you care about safety and proper form.
            Make it feel like a genuine message from a friend, not a professional coach.
            Keep it concise (2-3 sentences max) and use emojis.

            Your message should start with "Yo bro! 💪" or similar casual greeting."""

            if DEBUG_MODE:
                logger.info(f"LLM Prompt:\n{prompt}")

            response_text = await self._generate_with_retry(prompt, temperature=1.2)
            return response_text

        except Exception as e:
            logger.error(f"Error getting daily tip after all retries: {e}")
            return "Yo bro! Did you know that staying hydrated is key for gains? 💧💪 Keep that water bottle close! 🔥"
