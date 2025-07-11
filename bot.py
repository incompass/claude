import asyncio
import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TimedOut, NetworkError, RetryAfter
from database import init_database, get_user_info, get_order_details
from config import setup_logging
import time
import asyncio

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://hukah-pashq.amvera.io')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '5720640497'))

# Словарь для хранения ID приветственных сообщений
welcome_messages = {}

async def retry_request(func, max_retries=3, delay=5):
    """Повторить запрос с экспоненциальной задержкой"""
    for attempt in range(max_retries):
        try:
            return await func()
        except (TimedOut, NetworkError) as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except RetryAfter as e:
            logger.warning(f"Rate limited. Waiting {e.retry_after}s...")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise e

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"User {user_id} started the bot")
    
    try:
        response = requests.get(f"{WEB_APP_URL}/{user_id}/info", timeout=30)
        user_registered = response.status_code == 200
    except Exception as e:
        logger.error(f"Error checking user info: {e}")
        user_registered = False
    
    if user_registered:
        webapp_url = f"{WEB_APP_URL}/{user_id}"
        message = f"🎭 {user.first_name}, вы уже зарегистрированы!\n\n"
        message += "Откройте каталог для заказа кальянов:"
        
        keyboard = [[
            InlineKeyboardButton(
                "🔥 Открыть каталог",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        async def send_reply():
            return await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
        
        await retry_request(send_reply)
    else:
        registration_url = f"{WEB_APP_URL}/{user_id}/reg"
        message = f"👋 Добро пожаловать, {user.first_name}!\n\n"
        message += "📝 Для начала работы нужно заполнить ваши контактные данные."
        
        keyboard = [[
            InlineKeyboardButton(
                "📝 Заполнить данные",
                web_app=WebAppInfo(url=registration_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение и сохраняем его ID
        async def send_message():
            return await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
        
        sent_message = await retry_request(send_message)
        
        # Сохраняем ID приветственного сообщения
        welcome_messages[user_id] = sent_message.message_id
        logger.info(f"Saved welcome message ID {sent_message.message_id} for user {user_id}")
        
        # Сохраняем в базе данных через API
        try:
            logger.info(f"Attempting to save welcome message ID {sent_message.message_id} for user {user_id}")
            response = requests.post(f"{WEB_APP_URL}/{user_id}/save_welcome_message", 
                         json={'message_id': sent_message.message_id}, 
                         timeout=5)
            if response.status_code == 200:
                logger.info(f"Welcome message ID saved to database for user {user_id}")
                # Проверим, что сохранилось
                check_response = requests.get(f"{WEB_APP_URL}/{user_id}/get_welcome_message", timeout=5)
                if check_response.status_code == 200:
                    saved_data = check_response.json()
                    logger.info(f"Verification: saved welcome message ID is {saved_data.get('message_id')}")
                else:
                    logger.error(f"Failed to verify saved welcome message ID: {check_response.status_code}")
            else:
                logger.error(f"Failed to save welcome message ID: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error saving welcome message ID: {e}")

async def handle_order_notification(user_id: int, order_number: int, bot_token: str):
    try:
        order = get_order_details(user_id, order_number)
        user_info = get_user_info(user_id)
        
        if not order or not user_info:
            logger.error(f"Order {order_number} or user {user_id} not found")
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
        
        admin_webapp_url = f"{WEB_APP_URL}/{user_id}/{order_number}/adm"
        contact_url = f"tg://openmessage?user_id={user_id}"
        
        keyboard = [
            [InlineKeyboardButton("👀 Посмотреть заказ", web_app=WebAppInfo(url=admin_webapp_url))],
            [InlineKeyboardButton("💬 Написать клиенту", url=contact_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        from telegram import Bot
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        logger.info(f"Order notification sent to admin for order {order_number}")
        
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Игнорируем команду /start в обработчике сообщений (она обрабатывается отдельно)
    if update.message.text == "/start":
        return
    
    try:
        response = requests.get(f"{WEB_APP_URL}/{user_id}/info", timeout=10)
        user_registered = response.status_code == 200
    except Exception as e:
        logger.error(f"Error checking user info: {e}")
        user_registered = False
    
    if user_registered:
        webapp_url = f"{WEB_APP_URL}/{user_id}"
        message = "🎭 Используйте мини-приложение для заказа кальянов:"
        
        keyboard = [[
            InlineKeyboardButton(
                "🔥 Открыть каталог кальянов",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        async def send_reply():
            return await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
        
        await retry_request(send_reply)
    else:
        registration_url = f"{WEB_APP_URL}/{user_id}/reg"
        message = "📝 Сначала заполните ваши контактные данные:"
        
        keyboard = [[
            InlineKeyboardButton(
                "📝 Заполнить данные",
                web_app=WebAppInfo(url=registration_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        async def send_reply():
            return await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
        
        await retry_request(send_reply)

async def webhook_handler(request_data):
    try:
        if 'order_created' in request_data:
            user_id = request_data['user_id']
            order_number = request_data['order_number']
            
            application = Application.builder().token(BOT_TOKEN).build()
            await handle_order_notification(user_id, order_number, application)
            
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")

def get_welcome_message_id(user_id):
    """Получить ID приветственного сообщения для пользователя"""
    return welcome_messages.get(user_id)

def remove_welcome_message_id(user_id):
    """Удалить ID приветственного сообщения для пользователя"""
    if user_id in welcome_messages:
        del welcome_messages[user_id]

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    init_database()
    
    # Создаем приложение с увеличенными таймаутами
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30
    )
    
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot started")
    
    # Запускаем с обработкой ошибок
    max_retries = 5
    for attempt in range(max_retries):
        try:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            break
        except (TimedOut, NetworkError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to start bot after {max_retries} attempts: {e}")
                raise e
            wait_time = 10 * (2 ** attempt)
            logger.warning(f"Bot startup failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Unexpected error starting bot: {e}")
            raise e

if __name__ == '__main__':
    main() 