# Gym Stats & Motivation Bot 🏋️‍♂️

A dual-project system that combines real-time gym occupancy tracking with an AI-powered motivational Telegram bot. The system helps users monitor gym crowdedness and stay motivated in their fitness journey.

## Project Components

### 1. Gym Stats Scraper 📊

A Python-based scraper that collects real-time occupancy data from WellFitness API:
- Runs every 10 minutes to gather current gym attendance
- Stores data in Supabase for historical analysis
- Implements robust error handling and data validation
- Maintains both processed stats and raw API responses
- Uses session-based authentication with token management

### 2. Telegram Motivation Bot 🤖

An AI-powered Telegram bot that helps users stay motivated and track their gym goals:
- Uses Gemini AI for natural, gym bro-style conversations
- Implements a weekly goal system with accountability
- Provides daily motivational messages and gym tips
- Shows real-time gym occupancy stats
- Generates time series visualizations of gym attendance

## Features

### Gym Stats
- Real-time member count tracking
- Historical data analysis
- Time series visualizations
- Peak hours detection
- Data validation and error handling

### Telegram Bot
- Weekly gym goal setting (1-5 visits)
- Goal progress tracking
- Accountability system with temporary bans for missed goals
- Daily motivational messages (17:10)
- Random daily gym tips (12:00-18:00)
- Natural conversation with gym bro personality
- Real-time gym occupancy stats and graphs

## Technical Details

### Data Storage
- Supabase database with tables for:
  - Gym stats (time series data)
  - Raw API responses
  - User goals
  - Ban records
  - Message history

### API Integration
- WellFitness API for gym data
- Gemini AI for natural language processing
- Telegram Bot API for user interaction

### Rate Limiting
- Gym data: 10-minute intervals
- LLM requests: 14 RPM (requests per minute)
- Automatic retry mechanism for API failures

## Environment Variables

```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Telegram
TELEGRAM_BOT_TOKEN=your_production_bot_token
TELEGRAM_BOT_TOKEN_DEV=your_development_bot_token

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Environment
ENVIRONMENT=development|production
DEBUG_MODE=true|false
```

## Development

### Prerequisites
- Python 3.8+
- Supabase account
- Telegram Bot token
- Gemini AI API key

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables
4. Run the services:
   ```bash
   # Run the scraper
   python src/scraper.py

   # Run the Telegram bot
   python src/telegram_bot.py
   ```

### Testing
- Preview test system for LLM responses:
  ```bash
  python tests/preview/generate_previews.py
  ```

## Deployment

Both services are designed to run continuously:
- Scraper runs on a 10-minute cycle
- Telegram bot handles user interactions and scheduled tasks:
  - Daily motivation (17:10)
  - Daily tips (random time between 12:00-18:00)
  - Weekly goal checks (Saturday 23:50)

## Contributing

Feel free to submit issues and enhancement requests!

## License

[MIT License](LICENSE) 