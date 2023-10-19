from dotenv import find_dotenv, load_dotenv
import os

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()


TOKEN = os.getenv("TOKEN")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DBNAME = os.getenv("DBNAME")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")





