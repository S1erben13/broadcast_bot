from dotenv import load_dotenv
import os

TOKEN = os.getenv('SERVANT_TOKEN')

API_BASE_URL = "http://api:8000"

MESSAGES = {
    "welcome": "Добро пожаловать! Выберите действие:",
    "subscribed": "Вы подписались на рассылку!",
    "already_subscribed": "Вы уже подписаны на рассылку!",
    "unsubscribed": "Вы отписались от рассылки.",
    "not_subscribed": "Вы не были подписаны на рассылку.",
    "subscription_error": "Произошла ошибка при попытке подписки.",
    "unsubscription_error": "Произошла ошибка при отписке.",
}

BUTTONS = {
    "follow": "/follow",
    "unfollow": "/unfollow",
}