import os
import requests
import threading
from database import get_order_details, get_user_info, get_welcome_message_id, clear_welcome_message_id

def send_telegram_notification(user_id: int, order_number: int):
    """Отправляет уведомление администратору через Telegram API"""
    try:
        bot_token = os.environ.get('BOT_TOKEN')
        if not bot_token:
            print("Bot token not found")
            return
        
        admin_id = 7059439474
        web_app_url = 'https://hukah-pashq.amvera.io'
        
        order = get_order_details(user_id, order_number)
        user_info = get_user_info(user_id)
        
        if not order or not user_info:
            print(f"Order {order_number} or user {user_id} not found")
            return
        
        admin_message = f"🔔 <b>Новый заказ!</b>\n\n"
        admin_message += f"👤 <b>От:</b> {user_info['last_name']} {user_info['first_name']}"
        if user_info['middle_name']:
            admin_message += f" {user_info['middle_name']}"
        admin_message += f"\n📞 <b>Телефон:</b> {user_info['phone']}"
        admin_message += f"\n🆔 <b>Telegram ID:</b> {user_id}"
        if user_info['username']:
            admin_message += f" (@{user_info['username']})"
        admin_message += f"\n\n📋 <b>Заказ #{order['order_number']}</b>"
        admin_message += f"\n📅 <b>Доставка:</b> {order['delivery_date']} в {order['delivery_time']}"
        admin_message += f"\n📍 <b>Адрес:</b> {order['address']}"
        admin_message += f"\n⏰ <b>Срок аренды:</b> {order['rental_days']} дн."
        admin_message += f"\n💰 <b>Сумма:</b> {order['total_price']}₽"
        
        admin_message += f"\n\n🎭 <b>Кальяны:</b>"
        for hookah in order['hookahs']:
            admin_message += f"\n• {hookah['name']} - {hookah['tariff']}"
            if hookah['fruit_bowl']:
                admin_message += f" + {hookah['fruit_bowl']}"
        
        if order['drinks']:
            admin_message += f"\n\n🥤 <b>Напитки:</b>"
            for drink in order['drinks']:
                admin_message += f"\n• {drink['name']} × {drink['quantity']}"
        
        if order['preparation_service']:
            admin_message += f"\n\n✨ Приготовка кальяна: +290₽"
        
        if order['additional_tobacco'] > 0:
            admin_message += f"\n🍃 Дополнительный табак: {order['additional_tobacco']} пачек (+{order['additional_tobacco'] * 350}₽)"
        
        # Создаем inline keyboard
        admin_webapp_url = f"{web_app_url}/{user_id}/{order_number}/adm"
        contact_url = f"tg://openmessage?user_id={user_id}"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "👀 Посмотреть заказ", "web_app": {"url": admin_webapp_url}}],
                [{"text": "💬 Написать клиенту", "url": contact_url}]
            ]
        }
        
        # Отправляем сообщение через Telegram API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": admin_id,
            "text": admin_message,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"Order notification sent to admin for order {order_number}")
        else:
            print(f"Failed to send notification: {response.text}")
            
    except Exception as e:
        print(f"Error sending order notification: {e}")

def send_notification_async(user_id: int, order_number: int):
    """Отправляет уведомление в отдельном потоке"""
    thread = threading.Thread(target=send_telegram_notification, args=(user_id, order_number))
    thread.daemon = True
    thread.start()

def send_registration_success(telegram_id: int):
    """Отправляет уведомление об успешной регистрации"""
    print(f"=== STARTING REGISTRATION SUCCESS FOR USER {telegram_id} ===")
    try:
        bot_token = os.environ.get('BOT_TOKEN')
        if not bot_token:
            print("Bot token not found")
            return
        
        web_app_url = 'https://hukah-pashq.amvera.io'
        
        # Пытаемся удалить/отредактировать приветственное сообщение
        welcome_message_id = get_welcome_message_id(telegram_id)
        print(f"Attempting to handle welcome message for user {telegram_id}, message_id: {welcome_message_id}")
        
        message_handled = False
        
        if welcome_message_id:
            # Сначала пробуем удалить сообщение
            delete_url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
            delete_data = {
                "chat_id": telegram_id,
                "message_id": welcome_message_id
            }
            
            try:
                print(f"Sending delete request to: {delete_url}")
                print(f"Delete data: {delete_data}")
                delete_response = requests.post(delete_url, json=delete_data, timeout=10)
                print(f"Delete response status: {delete_response.status_code}")
                print(f"Delete response text: {delete_response.text}")
                
                if delete_response.status_code == 200:
                    print(f"Welcome message {welcome_message_id} deleted for user {telegram_id}")
                    clear_welcome_message_id(telegram_id)
                    message_handled = True
                else:
                    print(f"Failed to delete welcome message: {delete_response.text}")
                    # Если удаление не удалось, пробуем отредактировать
                    edit_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
                    edit_data = {
                        "chat_id": telegram_id,
                        "message_id": welcome_message_id,
                        "text": "✅ Регистрация завершена!",
                        "reply_markup": {"inline_keyboard": []}
                    }
                    
                    print(f"Sending edit request to: {edit_url}")
                    print(f"Edit data: {edit_data}")
                    edit_response = requests.post(edit_url, json=edit_data, timeout=10)
                    print(f"Edit response status: {edit_response.status_code}")
                    print(f"Edit response text: {edit_response.text}")
                    
                    if edit_response.status_code == 200:
                        print(f"Welcome message {welcome_message_id} edited for user {telegram_id}")
                        clear_welcome_message_id(telegram_id)
                        message_handled = True
                    else:
                        print(f"Failed to edit welcome message: {edit_response.text}")
                        
            except Exception as e:
                print(f"Error handling welcome message: {e}")
        else:
            print(f"No welcome message ID found for user {telegram_id}")
        
        # Отправляем сообщение о завершении регистрации только если не смогли отредактировать приветственное
        if not message_handled:
            message = f"""
✅ <b>Регистрация завершена!</b>

Поздравляем! Ваши данные успешно сохранены.

Теперь вы можете пользоваться всеми функциями системы заказа кальянов:
• 🎭 Выбирать кальяны с разными тарифами
• 🥤 Добавлять напитки
• ❤️ Сохранять в избранное
• 🛒 Оформлять заказы
• 📍 Управлять адресами доставки

Перейдите в каталог для выбора кальянов! 🔥
"""
            
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "🎭 Открыть каталог",
                            "web_app": {"url": f"{web_app_url}/{telegram_id}"}
                        }
                    ]
                ]
            }
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": telegram_id,
                "text": message,
                "reply_markup": keyboard,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"Registration success notification sent to {telegram_id}")
            else:
                print(f"Failed to send registration notification: {response.text}")
        else:
            print(f"Welcome message was handled successfully, no need to send additional message")
            
    except Exception as e:
        print(f"Error sending registration notification: {e}")

def send_registration_success_async(telegram_id: int):
    """Отправляет уведомление о регистрации в отдельном потоке"""
    print(f"=== TRIGGERING ASYNC REGISTRATION SUCCESS FOR USER {telegram_id} ===")
    thread = threading.Thread(target=send_registration_success, args=(telegram_id,))
    thread.daemon = True
    thread.start()
    print(f"=== ASYNC THREAD STARTED FOR USER {telegram_id} ===") 