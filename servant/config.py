import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

Messages = Dict[str, str]
Buttons = Dict[str, str]

TOKEN: str = os.getenv("SERVANT_TOKEN")
REG_SERVANT_TOKEN = os.getenv('REG_SERVANT_TOKEN')
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://api:8000")
CHECK_MSGS_RATE = int(os.getenv("CHECK_MSGS_RATE", 60))

MESSAGES: Messages = {
    "welcome": "Добро пожаловать! Выберите действие:",
    "subscribed": "Вы подписались на рассылку!",
    "already_subscribed": "Вы уже подписаны на рассылку!",
    "already_unsubscribed": "Вы уже отписаны от рассылки!",
    "unsubscribed": "Вы отписались от рассылки.",
    "not_subscribed": "Вы не были подписаны на рассылку.",
    "subscription_error": "Произошла ошибка при попытке подписки.",
    "unsubscription_error": "Произошла ошибка при отписке.",
    "invalid_token": "Invalid registration token. Please provide a valid token to subscribe.",
}

BUTTONS: Buttons = {
    "follow": "/follow",
    "unfollow": "/unfollow",
}

if not TOKEN:
    raise ValueError("SERVANT_TOKEN environment variable is not set.")

