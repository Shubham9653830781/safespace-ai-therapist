import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env from project root or backend directory if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

# Enter your API keys here or configure them in a .env file:
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Twilio Credentials (Optional - for emergency voice calling & WhatsApp)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")  # your Twilio number
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT", "")  # or your local emergency number
