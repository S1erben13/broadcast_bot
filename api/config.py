import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"

# Security
SECRET_KEY = os.getenv("SECRET_KEY")

# Application messages
ERROR_MESSAGES = {
    "chat_id_exists": "Chat with this ID already exists",
    "user_id_exists": "User with this ID already exists",
    "database_integrity_error": "Database integrity error",
    "user_not_found": "User not found",
    "internal_server_error": "Internal server error",
    "message_send_error": "Message sending error",
    "master_not_found": "Master not found",
    "invalid_input": "Invalid input data",
    "subscription_error": "Subscription error",
    "unsubscription_error": "Unsubscription error",
}

SUCCESS_MESSAGES = {
    "user_deleted": "User successfully deleted",
    "user_updated": "User data updated",
    "master_updated": "Master data updated",
    "message_sent": "Message sent successfully",
    "subscribed": "Subscribed successfully",
    "unsubscribed": "Unsubscribed successfully",
}