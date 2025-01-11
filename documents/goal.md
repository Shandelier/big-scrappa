## Project Goal
The primary goal of this project is to develop a robust and scalable web scraper that collects data from a fitness club management system. The scraper will be deployed in a cloud environment, such as Google Cloud Platform (GCP) or Hetzner, and will provide real-time insights into club usage statistics. Additionally, the project aims to integrate with Telegram and OpenAI APIs to deliver engaging and informative updates to users.

## Current Status of the Works
1. **Web Scraping**: 
   - Implemented a Python-based scraper with session-based authentication to handle token expiration.
   - Successfully collects data every 10 minutes and processes it into structured CSV files.

2. **Data Management**:
   - Stores processed data in `clubs.csv` and `stats.csv` in the `data/` directory.
   - Maintains a backup of raw JSON responses with daily backups and a 7-day retention policy in the `backups/` directory.
   - Implements efficient data storage by separating static club information from dynamic usage statistics.

4. **Monitoring and Logging**:
   - Implemented structured logging with log rotation for both file and console outputs.
   - Added a health check endpoint for monitoring the container's status.
   - Dual-format logging: traditional format for local development and JSON format for cloud environments.

5. **Security and Configuration**:
   - Utilizes environment variables for managing sensitive information.
   - Provided a `.env.example` file for configuration guidance.
   - Implements secure session-based authentication.

6. **Telegram Bot Integration**:
   - Successfully implemented a Telegram bot for user interaction.
   - Provides real-time club statistics and usage data through chat commands.
   - Generates time series visualizations of club attendance.

## Next Steps

add a /goal functionalityt to the bot. it let's you make a bet that you will go to the gym 1-5 (user selects) times this week. if you don't go to the gym, you lose the bet. When you loose the bet you won't be able to interact with the bot. (he's dissapointed at you. it should generate a image showing you how much it's dissapointed)

This setup will enable real-time data collection and analysis, providing users with insightful and entertaining updates on club usage.
