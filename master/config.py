import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram bot token
TOKEN = os.getenv('MASTER_TOKEN')
if not TOKEN:
    raise ValueError("MASTER_TOKEN environment variable is not set.")

# API endpoint for sending messages
API_URL = 'http://api:8000/messages'

# Messages for user responses
MESSAGES = {
    "message_sent": "Message sent successfully! API response: {api_response}",
    "message_send_error": "An error occurred while sending the message. Please try again later.",
}

# HTTP request timeout
HTTP_TIMEOUT = 10.0

# Format for displaying API response
API_RESPONSE_FORMAT = "API response: {api_response}"