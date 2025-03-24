import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram bot token
TOKEN = os.getenv('MASTER_TOKEN')
if not TOKEN:
    raise ValueError("MASTER_TOKEN environment variable is not set.")

REG_MASTER_TOKEN = os.getenv('REG_MASTER_TOKEN')

# API endpoint for sending messages
API_URL = 'http://api:8000/'

# Messages for user responses
MESSAGES = {
    "message_sent": "Message sent successfully!",
    "message_send_error": "An error occurred while sending the message. Please try again later.",
    "not_master": "Only Master's can send message",
    "master_activated" : "Master created",
    "master_deactivated" : "Master deleted",
    "master_already_activated" : "Master exists",
    "master_already_deactivated" : "Master does not exists",
    "handle_error" : "Handle error",
}

# HTTP request timeout
HTTP_TIMEOUT = 10.0