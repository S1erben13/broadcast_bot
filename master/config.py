import os
from dotenv import load_dotenv

TOKEN = os.getenv('MASTER_TOKEN')
API_URL = 'http://api:8000/messages'

MESSAGES = {
    "message_sent": "Сообщение успешно отправлено! Ответ API: {api_response}",
    "message_send_error": "Произошла ошибка при отправке сообщения. Попробуйте позже.",
}

HTTP_TIMEOUT = 10.0

API_RESPONSE_FORMAT = "Ответ API: {api_response}"