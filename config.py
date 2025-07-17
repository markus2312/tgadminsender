import os

# Получаем из переменных окружения
API_ID = int(os.getenv("TG_API_ID", 0))
API_HASH = os.getenv("TG_API_HASH", "")
SESSION_NAME = os.getenv("TG_SESSION_NAME", "79398382811")  # по умолчанию имя файла сессии без .session
