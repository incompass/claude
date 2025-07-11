#!/usr/bin/env python3
import sqlite3
import os

# Путь к базе данных
DATABASE_PATH = '/data/hookah_system.db'

# Если база данных не существует, создаем ее
if not os.path.exists(DATABASE_PATH):
    DATABASE_PATH = 'hookah_system.db'

print(f"Using database: {DATABASE_PATH}")

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Проверяем структуру таблицы users
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Users table structure:")
for col in columns:
    print(f"  {col}")

# Проверяем данные пользователя
telegram_id = 5720640497
cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
user_data = cursor.fetchone()
print(f"\nUser data for {telegram_id}:")
print(user_data)

# Проверяем все записи в таблице users
cursor.execute("SELECT telegram_id, welcome_message_id FROM users")
all_users = cursor.fetchall()
print(f"\nAll users with welcome_message_id:")
for user in all_users:
    print(f"  User {user[0]}: welcome_message_id = {user[1]}")

conn.close() 