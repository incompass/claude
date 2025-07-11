#!/usr/bin/env python3
import requests
import sys

if len(sys.argv) != 3:
    print("Usage: python fix_welcome_message.py <telegram_id> <message_id>")
    sys.exit(1)

telegram_id = int(sys.argv[1])
message_id = int(sys.argv[2])
base_url = "https://hukah-pashq.amvera.io"

print(f"Fixing welcome message ID for user {telegram_id}, message ID: {message_id}")

# Принудительно сохраняем ID
response = requests.post(f"{base_url}/{telegram_id}/save_welcome_message", 
                        json={'message_id': message_id})
if response.status_code == 200:
    print("Message ID saved successfully")
else:
    print(f"Failed to save message ID: {response.status_code} - {response.text}")

# Проверяем, что сохранилось
response = requests.get(f"{base_url}/{telegram_id}/get_welcome_message")
if response.status_code == 200:
    data = response.json()
    saved_id = data.get('message_id')
    print(f"Verification: saved welcome message ID is {saved_id}")
else:
    print(f"Failed to get welcome message ID: {response.status_code}")

# Тестируем удаление
print("Testing deletion...")
response = requests.post(f"{base_url}/{telegram_id}/test_delete_welcome")
if response.status_code == 200:
    data = response.json()
    print(f"Test delete result: {data}")
else:
    print(f"Failed to test delete: {response.status_code} - {response.text}") 