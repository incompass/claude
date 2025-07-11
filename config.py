# config.py

import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys

# Загружаем переменные окружения из .env файла
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Не задан токен бота! Добавьте BOT_TOKEN в .env файл")

# Пути к файлам данных - путь для Amvera
DATA_DIR = '/data'
os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_IDS_FILE = os.path.join(DATA_DIR, 'admin_ids.json')
HOOKAHS_FILE = os.path.join(DATA_DIR, 'hookahs.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.txt')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
PASSWORD_ATTEMPTS_FILE = os.path.join(DATA_DIR, 'password_attempts.json')
LOGS_FILE = os.path.join(DATA_DIR, 'bot.log')

# Настройки администраторов
ADMIN_PASSWORD = "1025"  # Пароль для добавления админа
DEFAULT_ADMIN_IDS = [5720640497, 7059439474]  # ID админов по умолчанию

# Максимальное количество попыток для повторной отправки сообщений
MAX_RETRIES = 3

def setup_logging():
    """Настраивает логирование"""
    # Создаем директорию для логов, если она не существует
    os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
    
    # Настраиваем логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Форматирование логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Обработчик для вывода в файл
    file_handler = RotatingFileHandler(
        LOGS_FILE, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики в логгер
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Отключаем избыточные логи от библиотек
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('telegram.bot').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext').setLevel(logging.WARNING)
    
    return logger