import os
from dotenv import load_dotenv

postgres_user = os.getenv("POSTGRES_USER")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_db = os.getenv("POSTGRES_DB")

url = f'postgresql+asyncpg://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}'