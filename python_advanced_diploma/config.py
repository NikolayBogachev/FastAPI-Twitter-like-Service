from dotenv import load_dotenv
import os

load_dotenv()

URL = os.environ.get("URL")
URL2 = os.environ.get("URL2")
DB_NAME = os.environ.get("DB_NAME")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")
TOKEN = os.environ.get("TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
