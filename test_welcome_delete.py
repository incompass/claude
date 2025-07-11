#!/usr/bin/env python3
import requests
import sys

if len(sys.argv) != 2:
    print("Usage: python test_welcome_delete.py <telegram_id>")
    sys.exit(1)

telegram_id = int(sys.argv[1])
base_url = "https://hukah-pashq.amvera.io"

print(f"Testing welcome message deletion for user {telegram_id}")

# Проверяем, есть ли сохраненный ID
response = requests.get(f"{base_url}/{telegram_id}/get_welcome_message")
if response.status_code == 200:
    data = response.json()
    message_id = data.get('message_id')
    print(f"Saved welcome message ID: {message_id}")
else:
    print(f"Failed to get welcome message ID: {response.status_code}")

# Тестируем удаление
response = requests.post(f"{base_url}/{telegram_id}/test_delete_welcome")
if response.status_code == 200:
    data = response.json()
    print(f"Test delete result: {data}")
else:
    print(f"Failed to test delete: {response.status_code} - {response.text}") 