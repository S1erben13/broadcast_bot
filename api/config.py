import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

postgres_user = os.getenv("POSTGRES_USER")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_db = os.getenv("POSTGRES_DB")

url = f'postgresql+asyncpg://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}'

private_key_path = BASE_DIR / "api" / "certs" / "jwt-private.pem"
public_key_path = BASE_DIR / "api" / "certs" / "jwt-public.pem"

algorithm = 'RS256'
access_token_expire_minutes: int = 15

ERROR_MESSAGES = {
    "chat_id_exists": "Чат с таким ID уже существует.",
    "user_id_exists": "Пользователь с таким ID уже существует.",
    "database_integrity_error": "Ошибка целостности базы данных.",
    "user_not_found": "Пользователь не найден.",
    "internal_server_error": "Внутренняя ошибка сервера.",
    "message_send_error": "Ошибка при отправке сообщения на servant.",
    "master_not_found": "Мастер не найден.",
    "invalid_input": "Некорректные данные. Проверьте ввод и попробуйте снова.",
    "subscription_error": "Ошибка при попытке подписки.",
    "unsubscription_error": "Ошибка при попытке отписки.",
    "follow_error": "Ошибка при попытке подписки на обновления.",
    "unfollow_error": "Ошибка при попытке отписки от обновлений.",
}

SUCCESS_MESSAGES = {
    "user_deleted": "Пользователь успешно удален.",
    "pong": "pong!",
    "user_updated": "Данные пользователя успешно обновлены.",
    "master_updated": "Данные мастера успешно обновлены.",
    "message_sent": "Сообщение успешно отправлено.",
    "subscribed": "Вы успешно подписались на рассылку.",
    "unsubscribed": "Вы успешно отписались от рассылки.",
    "followed": "Вы успешно подписались на обновления.",
    "unfollowed": "Вы успешно отписались от обновлений.",
}
