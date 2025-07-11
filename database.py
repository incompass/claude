import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

DATABASE_PATH = '/data/hookah_system.db'

def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            phone TEXT,
            first_name TEXT,
            last_name TEXT,
            middle_name TEXT,
            username TEXT,
            welcome_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Миграция: добавляем колонку welcome_message_id если её нет
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN welcome_message_id INTEGER')
        print("Added welcome_message_id column to users table")
    except sqlite3.OperationalError:
        # Колонка уже существует
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hookahs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            photo_url TEXT,
            price_no_tobacco INTEGER NOT NULL,
            price_standard INTEGER NOT NULL,
            price_premium INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_number INTEGER,
            delivery_date TEXT,
            delivery_time TEXT,
            rental_days INTEGER,
            address TEXT,
            total_price INTEGER,
            preparation_service BOOLEAN DEFAULT FALSE,
            additional_tobacco INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            hookah_id INTEGER,
            tariff TEXT,
            price INTEGER,
            fruit_bowl TEXT,
            fruit_price INTEGER DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (hookah_id) REFERENCES hookahs (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            drink_id INTEGER,
            quantity INTEGER,
            price INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (drink_id) REFERENCES drinks (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hookah_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id),
            FOREIGN KEY (hookah_id) REFERENCES hookahs (id),
            UNIQUE(user_id, hookah_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hookah_id INTEGER,
            tariff TEXT,
            fruit_bowl TEXT,
            fruit_price INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id),
            FOREIGN KEY (hookah_id) REFERENCES hookahs (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            drink_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id),
            FOREIGN KEY (drink_id) REFERENCES drinks (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    populate_initial_data()

def populate_initial_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    hookahs_data = [
        ('RuLuxe BROWN', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('RuLuxe RED', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('RuLuxe BLUE', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('RuLuxe VIOLET', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('7STAR RED', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('7STAR BLACK', '— Кальян больше среднего размера\n— Глиняная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('BlackNinja', '— Кальян среднего размера\n— Глиняная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('PunkLi WOOD', '— Кальян среднего размера\n— Глиняная глазурированная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
        ('MISHA Revolt Hero Flash', '— Кальян чуть больше среднего размера\n— Глиняная чаша\n— Отличная вкусопередача\n— Подходит для дома, а так же и для улицы', None, 900, 1200, 1900),
    ]
    
    cursor.execute('SELECT COUNT(*) FROM hookahs')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO hookahs (name, description, photo_url, price_no_tobacco, price_standard, price_premium)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', hookahs_data)
    
    drinks_data = [
        ('Monster Energy', 350),
        ('Arizona Tea', 450),
        ('Bubble Tea', 450),
    ]
    
    cursor.execute('SELECT COUNT(*) FROM drinks')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO drinks (name, price)
            VALUES (?, ?)
        ''', drinks_data)
    
    conn.commit()
    conn.close()

def get_user_info(telegram_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT telegram_id, phone, first_name, last_name, middle_name, username
        FROM users WHERE telegram_id = ?
    ''', (telegram_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'telegram_id': row[0],
            'phone': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'middle_name': row[4],
            'username': row[5]
        }
    return None

def save_user_info(telegram_id: int, phone: str, first_name: str, last_name: str, middle_name: str = None, username: str = None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (telegram_id, phone, first_name, last_name, middle_name, username)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (telegram_id, phone, first_name, last_name, middle_name, username))
    
    conn.commit()
    conn.close()

def get_hookahs() -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, description, photo_url, price_no_tobacco, price_standard, price_premium
        FROM hookahs WHERE is_active = TRUE
    ''')
    
    hookahs = []
    for row in cursor.fetchall():
        hookahs.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'photo_url': row[3],
            'price_no_tobacco': row[4],
            'price_standard': row[5],
            'price_premium': row[6]
        })
    
    conn.close()
    return hookahs

def get_hookah_by_id(hookah_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, description, photo_url, price_no_tobacco, price_standard, price_premium
        FROM hookahs WHERE id = ? AND is_active = TRUE
    ''', (hookah_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'photo_url': row[3],
            'price_no_tobacco': row[4],
            'price_standard': row[5],
            'price_premium': row[6]
        }
    return None

def get_drinks() -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, price
        FROM drinks WHERE is_active = TRUE
    ''')
    
    drinks = []
    for row in cursor.fetchall():
        drinks.append({
            'id': row[0],
            'name': row[1],
            'price': row[2]
        })
    
    conn.close()
    return drinks

def get_user_addresses(telegram_id: int) -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, address FROM addresses WHERE user_id = ?
    ''', (telegram_id,))
    
    addresses = []
    for row in cursor.fetchall():
        addresses.append({
            'id': row[0],
            'address': row[1]
        })
    
    conn.close()
    return addresses

def add_user_address(telegram_id: int, address: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO addresses (user_id, address) VALUES (?, ?)
    ''', (telegram_id, address))
    
    conn.commit()
    conn.close()

def delete_user_address(telegram_id: int, address_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM addresses WHERE id = ? AND user_id = ?
    ''', (address_id, telegram_id))
    
    conn.commit()
    conn.close()

def get_user_favorites(telegram_id: int) -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT h.id, h.name, h.description, h.price_no_tobacco, h.price_standard, h.price_premium
        FROM favorites f
        JOIN hookahs h ON f.hookah_id = h.id
        WHERE f.user_id = ?
    ''', (telegram_id,))
    
    favorites = []
    for row in cursor.fetchall():
        favorites.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price_no_tobacco': row[3],
            'price_standard': row[4],
            'price_premium': row[5]
        })
    
    conn.close()
    return favorites

def toggle_favorite(telegram_id: int, hookah_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM favorites WHERE user_id = ? AND hookah_id = ?
    ''', (telegram_id, hookah_id))
    
    if cursor.fetchone():
        cursor.execute('''
            DELETE FROM favorites WHERE user_id = ? AND hookah_id = ?
        ''', (telegram_id, hookah_id))
    else:
        cursor.execute('''
            INSERT INTO favorites (user_id, hookah_id) VALUES (?, ?)
        ''', (telegram_id, hookah_id))
    
    conn.commit()
    conn.close()

def get_user_cart(telegram_id: int) -> Dict:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, h.id, h.name, h.description, c.tariff, c.fruit_bowl, c.fruit_price,
               CASE 
                   WHEN c.tariff = 'no_tobacco' THEN h.price_no_tobacco
                   WHEN c.tariff = 'standard' THEN h.price_standard
                   WHEN c.tariff = 'premium' THEN h.price_premium
               END as base_price
        FROM cart c
        JOIN hookahs h ON c.hookah_id = h.id
        WHERE c.user_id = ?
    ''', (telegram_id,))
    
    hookahs = []
    for row in cursor.fetchall():
        hookahs.append({
            'cart_id': row[0],
            'hookah_id': row[1],
            'name': row[2],
            'description': row[3],
            'tariff': row[4],
            'fruit_bowl': row[5],
            'fruit_price': row[6],
            'base_price': row[7]
        })
    
    cursor.execute('''
        SELECT cd.id, d.id, d.name, d.price, cd.quantity
        FROM cart_drinks cd
        JOIN drinks d ON cd.drink_id = d.id
        WHERE cd.user_id = ?
    ''', (telegram_id,))
    
    drinks = []
    for row in cursor.fetchall():
        drinks.append({
            'cart_id': row[0],
            'drink_id': row[1],
            'name': row[2],
            'price': row[3],
            'quantity': row[4]
        })
    
    conn.close()
    return {'hookahs': hookahs, 'drinks': drinks}

def add_to_cart(telegram_id: int, hookah_id: int, tariff: str, fruit_bowl: str = None, fruit_price: int = 0):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO cart (user_id, hookah_id, tariff, fruit_bowl, fruit_price)
        VALUES (?, ?, ?, ?, ?)
    ''', (telegram_id, hookah_id, tariff, fruit_bowl, fruit_price))
    
    conn.commit()
    conn.close()

def add_drink_to_cart(telegram_id: int, drink_id: int, quantity: int = 1):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, quantity FROM cart_drinks WHERE user_id = ? AND drink_id = ?
    ''', (telegram_id, drink_id))
    
    existing = cursor.fetchone()
    if existing:
        cursor.execute('''
            UPDATE cart_drinks SET quantity = quantity + ? WHERE id = ?
        ''', (quantity, existing[0]))
    else:
        cursor.execute('''
            INSERT INTO cart_drinks (user_id, drink_id, quantity) VALUES (?, ?, ?)
        ''', (telegram_id, drink_id, quantity))
    
    conn.commit()
    conn.close()

def clear_cart(telegram_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (telegram_id,))
    cursor.execute('DELETE FROM cart_drinks WHERE user_id = ?', (telegram_id,))
    
    conn.commit()
    conn.close()

def create_order(telegram_id: int, delivery_date: str, delivery_time: str, rental_days: int, 
                address: str, preparation_service: bool = False, additional_tobacco: int = 0) -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COALESCE(MAX(order_number), 0) + 1 FROM orders WHERE user_id = ?
    ''', (telegram_id,))
    order_number = cursor.fetchone()[0]
    
    cart = get_user_cart(telegram_id)
    
    total_price = 0
    for hookah in cart['hookahs']:
        hookah_price = hookah['base_price'] * rental_days + hookah['fruit_price']
        total_price += hookah_price
    
    for drink in cart['drinks']:
        total_price += drink['price'] * drink['quantity']
    
    if preparation_service:
        total_price += 290
    
    if additional_tobacco > 0:
        total_price += additional_tobacco * 350
    
    cursor.execute('''
        INSERT INTO orders (user_id, order_number, delivery_date, delivery_time, rental_days, 
                           address, total_price, preparation_service, additional_tobacco)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (telegram_id, order_number, delivery_date, delivery_time, rental_days, 
          address, total_price, preparation_service, additional_tobacco))
    
    order_id = cursor.lastrowid
    
    for hookah in cart['hookahs']:
        cursor.execute('''
            INSERT INTO order_items (order_id, hookah_id, tariff, price, fruit_bowl, fruit_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, hookah['hookah_id'], hookah['tariff'], hookah['base_price'], 
              hookah['fruit_bowl'], hookah['fruit_price']))
    
    for drink in cart['drinks']:
        cursor.execute('''
            INSERT INTO order_drinks (order_id, drink_id, quantity, price)
            VALUES (?, ?, ?, ?)
        ''', (order_id, drink['drink_id'], drink['quantity'], drink['price']))
    
    conn.commit()
    conn.close()
    
    clear_cart(telegram_id)
    
    return order_number

def get_order_details(telegram_id: int, order_number: int) -> Optional[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT o.id, o.order_number, o.delivery_date, o.delivery_time, o.rental_days,
               o.address, o.total_price, o.preparation_service, o.additional_tobacco,
               o.status, o.created_at
        FROM orders o
        WHERE o.user_id = ? AND o.order_number = ?
    ''', (telegram_id, order_number))
    
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return None
    
    order = {
        'id': order_row[0],
        'order_number': order_row[1],
        'delivery_date': order_row[2],
        'delivery_time': order_row[3],
        'rental_days': order_row[4],
        'address': order_row[5],
        'total_price': order_row[6],
        'preparation_service': order_row[7],
        'additional_tobacco': order_row[8],
        'status': order_row[9],
        'created_at': order_row[10]
    }
    
    cursor.execute('''
        SELECT h.name, oi.tariff, oi.price, oi.fruit_bowl, oi.fruit_price
        FROM order_items oi
        JOIN hookahs h ON oi.hookah_id = h.id
        WHERE oi.order_id = ?
    ''', (order['id'],))
    
    order['hookahs'] = []
    for row in cursor.fetchall():
        order['hookahs'].append({
            'name': row[0],
            'tariff': row[1],
            'price': row[2],
            'fruit_bowl': row[3],
            'fruit_price': row[4]
        })
    
    cursor.execute('''
        SELECT d.name, od.quantity, od.price
        FROM order_drinks od
        JOIN drinks d ON od.drink_id = d.id
        WHERE od.order_id = ?
    ''', (order['id'],))
    
    order['drinks'] = []
    for row in cursor.fetchall():
        order['drinks'].append({
            'name': row[0],
            'quantity': row[1],
            'price': row[2]
        })
    
    conn.close()
    return order

def get_user_orders(telegram_id: int) -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT order_number, delivery_date, delivery_time, total_price, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (telegram_id,))
    
    orders = []
    for row in cursor.fetchall():
        orders.append({
            'order_number': row[0],
            'delivery_date': row[1],
            'delivery_time': row[2],
            'total_price': row[3],
            'status': row[4],
            'created_at': row[5]
        })
    
    conn.close()
    return orders

def remove_from_cart(telegram_id: int, item_type: str, cart_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if item_type == 'hookah':
        cursor.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, telegram_id))
    elif item_type == 'drink':
        cursor.execute('DELETE FROM cart_drinks WHERE id = ? AND user_id = ?', (cart_id, telegram_id))
    
    conn.commit()
    conn.close()

def update_drink_quantity(telegram_id: int, cart_id: int, quantity: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE cart_drinks SET quantity = ? 
        WHERE id = ? AND user_id = ?
    ''', (quantity, cart_id, telegram_id))
    
    conn.commit()
    conn.close()

def save_welcome_message_id(telegram_id: int, message_id: int):
    """Сохранить ID приветственного сообщения для пользователя"""
    print(f"Saving welcome message ID {message_id} for user {telegram_id}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Сначала проверим, существует ли пользователь
    cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
    user_exists = cursor.fetchone() is not None
    
    if user_exists:
        # Пользователь существует, обновляем
        cursor.execute('''
            UPDATE users SET welcome_message_id = ? WHERE telegram_id = ?
        ''', (message_id, telegram_id))
        print(f"Updated welcome_message_id to {message_id} for existing user {telegram_id}")
    else:
        # Пользователя нет, создаем запись
        cursor.execute('''
            INSERT INTO users (telegram_id, welcome_message_id) VALUES (?, ?)
        ''', (telegram_id, message_id))
        print(f"Created new user record with welcome_message_id {message_id} for user {telegram_id}")
    
    conn.commit()
    conn.close()
    
    # Проверяем, что сохранилось
    saved_id = get_welcome_message_id(telegram_id)
    print(f"Verification: saved welcome_message_id for user {telegram_id} is {saved_id}")

def get_welcome_message_id(telegram_id: int) -> Optional[int]:
    """Получить ID приветственного сообщения для пользователя"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT welcome_message_id FROM users WHERE telegram_id = ?
    ''', (telegram_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    result = row[0] if row and row[0] else None
    print(f"Retrieved welcome_message_id for user {telegram_id}: {result}")
    return result

def clear_welcome_message_id(telegram_id: int):
    """Очистить ID приветственного сообщения для пользователя"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET welcome_message_id = NULL WHERE telegram_id = ?
    ''', (telegram_id,))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database() 