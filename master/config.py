import os
from dotenv import load_dotenv

TOKEN = os.getenv('MASTER_TOKEN')
API_URL = 'http://api:8000/messages'