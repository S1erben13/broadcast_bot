import os

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoint for sending messages
API_URL = 'http://api:8000/'

SECRET_KEY = os.getenv('SECRET_KEY')

def get_tokens():
    response = requests.get(
        url=API_URL + '/projects',
        headers={'X-Secret-Key': SECRET_KEY}
    )
    data = response.json()
    tokens = [project['master_token'] for project in data['projects']]
    reg_tokens = [project['master_reg_token'] for project in data['projects']]
    bots_quantity = range(len(tokens))
    return [(tokens[i], reg_tokens[i]) for i in bots_quantity]

TOKENS = get_tokens()

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
    "command_error" : "Command does not exist",
}

# HTTP request timeout
HTTP_TIMEOUT = 10.0