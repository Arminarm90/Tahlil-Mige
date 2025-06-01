# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHECK_PHONE_URL = os.getenv("CHECK_PHONE_URL")
DAY_CONTENT_BASE_URL = os.getenv("DAY_CONTENT_BASE_URL")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID")) # Convert to int