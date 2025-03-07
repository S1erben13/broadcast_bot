import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

postgres_user = os.getenv("POSTGRES_USER")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_db = os.getenv("POSTGRES_DB")

url = f'postgresql+asyncpg://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}'

private_key_path = BASE_DIR / "certs" / "jwt-private.pem"
public_key_path = BASE_DIR / "certs" / "jwt-public.pem"
algorithm = 'RS256'
access_token_expire_minutes: int = 15

ERROR_MESSAGES = {
    "chat_id_exists": "Chat ID already exists",
    "user_id_exists": "User ID already exists",
    "database_integrity_error": "Database integrity error",
    "user_not_found": "User not found",
    "internal_server_error": "Internal server error",
    "message_send_error": "Ошибка при отправке сообщения на servant",
}

SUCCESS_MESSAGES = {
    "user_deleted": "User deleted",
    "pong": "pong!",
}

