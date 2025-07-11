from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from database import (
    init_database, get_user_info, save_user_info, get_hookahs, get_drinks,
    get_user_addresses, add_user_address, delete_user_address,
    get_user_favorites, toggle_favorite, get_user_cart, add_to_cart,
    add_drink_to_cart, clear_cart, create_order, get_order_details, get_user_orders
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*")

FRUIT_PRICES = {
    'apple': 200,
    'orange': 200,
    'grapefruit': 250,
    'pineapple': 300
}

@app.route('/')
def index():
    return "Hookah System API"

@app.route('/<int:telegram_id>')
def main_app(telegram_id):
    user_info = get_user_info(telegram_id)
    if not user_info:
        return redirect(url_for('registration', telegram_id=telegram_id))
    
    hookahs = get_hookahs()
    drinks = get_drinks()
    favorites = get_user_favorites(telegram_id)
    cart = get_user_cart(telegram_id)
    addresses = get_user_addresses(telegram_id)
    
    return render_template('main.html', 
                         telegram_id=telegram_id,
                         user_info=user_info,
                         hookahs=hookahs,
                         drinks=drinks,
                         favorites=favorites,
                         cart=cart,
                         addresses=addresses,
                         fruit_prices=FRUIT_PRICES)

@app.route('/<int:telegram_id>/reg')
def registration(telegram_id):
    return render_template('registration.html', telegram_id=telegram_id)

@app.route('/<int:telegram_id>/info')
def user_info(telegram_id):
    user_data = get_user_info(telegram_id)
    if user_data:
        return jsonify(user_data)
    return jsonify({'error': 'User not found'}), 404

@app.route('/<int:telegram_id>/save_info', methods=['POST'])
def save_info(telegram_id):
    data = request.json
    save_user_info(
        telegram_id=telegram_id,
        phone=data.get('phone'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        username=data.get('username')
    )
    
    # Отправляем уведомление пользователю через бота
    try:
        from notifications import send_registration_success_async
        send_registration_success_async(telegram_id)
        print(f"Registration success notification triggered for user {telegram_id}")
    except Exception as e:
        print(f"Error sending registration notification: {e}")
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/save_welcome_message', methods=['POST'])
def save_welcome_message(telegram_id):
    data = request.json
    message_id = data.get('message_id')
    
    # Сохраняем message_id в базе данных
    from database import save_welcome_message_id
    save_welcome_message_id(telegram_id, message_id)
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/get_welcome_message')
def get_welcome_message(telegram_id):
    from database import get_welcome_message_id
    message_id = get_welcome_message_id(telegram_id)
    return jsonify({'message_id': message_id})

@app.route('/<int:telegram_id>/test_delete_welcome', methods=['POST'])
def test_delete_welcome(telegram_id):
    """Тестовый endpoint для принудительного удаления приветственного сообщения"""
    try:
        from notifications import send_registration_success
        send_registration_success(telegram_id)
        return jsonify({'success': True, 'message': 'Test delete triggered'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/<int:telegram_id>/toggle_favorite', methods=['POST'])
def toggle_favorite_route(telegram_id):
    data = request.json
    hookah_id = data.get('hookah_id')
    toggle_favorite(telegram_id, hookah_id)
    
    # Уведомляем через WebSocket
    notify_user_update(telegram_id, 'favorites_updated', {'hookah_id': hookah_id})
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/add_to_cart', methods=['POST'])
def add_to_cart_route(telegram_id):
    data = request.json
    hookah_id = data.get('hookah_id')
    tariff = data.get('tariff')
    fruit_bowl = data.get('fruit_bowl')
    fruit_price = FRUIT_PRICES.get(fruit_bowl, 0) if fruit_bowl else 0
    
    add_to_cart(telegram_id, hookah_id, tariff, fruit_bowl, fruit_price)
    
    # Уведомляем через WebSocket
    notify_user_update(telegram_id, 'cart_updated', {'action': 'add', 'type': 'hookah'})
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/add_drink_to_cart', methods=['POST'])
def add_drink_to_cart_route(telegram_id):
    data = request.json
    drink_id = data.get('drink_id')
    quantity = data.get('quantity', 1)
    
    add_drink_to_cart(telegram_id, drink_id, quantity)
    
    # Уведомляем через WebSocket
    notify_user_update(telegram_id, 'cart_updated', {'action': 'add', 'type': 'drink'})
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/get_cart')
def get_cart_route(telegram_id):
    cart = get_user_cart(telegram_id)
    return jsonify(cart)

@app.route('/<int:telegram_id>/get_favorites')
def get_favorites_route(telegram_id):
    favorites = get_user_favorites(telegram_id)
    return jsonify(favorites)

@app.route('/<int:telegram_id>/get_hookah/<int:hookah_id>')
def get_hookah_route(telegram_id, hookah_id):
    from database import get_hookah_by_id
    hookah = get_hookah_by_id(hookah_id)
    if not hookah:
        return jsonify(None), 404
    return jsonify(hookah)

@app.route('/<int:telegram_id>/remove_from_cart', methods=['POST'])
def remove_from_cart_route(telegram_id):
    data = request.json
    item_type = data.get('type')
    cart_id = data.get('cart_id')
    
    from database import remove_from_cart
    remove_from_cart(telegram_id, item_type, cart_id)
    
    # Уведомляем через WebSocket
    notify_user_update(telegram_id, 'cart_updated', {'action': 'remove', 'type': item_type})
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/update_drink_quantity', methods=['POST'])
def update_drink_quantity_route(telegram_id):
    data = request.json
    cart_id = data.get('cart_id')
    quantity = data.get('quantity')
    
    from database import update_drink_quantity
    update_drink_quantity(telegram_id, cart_id, quantity)
    
    # Уведомляем через WebSocket
    notify_user_update(telegram_id, 'cart_updated', {'action': 'update', 'type': 'drink'})
    
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/clear_cart', methods=['POST'])
def clear_cart_route(telegram_id):
    clear_cart(telegram_id)
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/addresses')
def get_addresses_route(telegram_id):
    addresses = get_user_addresses(telegram_id)
    return jsonify(addresses)

@app.route('/<int:telegram_id>/add_address', methods=['POST'])
def add_address_route(telegram_id):
    data = request.json
    address = data.get('address')
    add_user_address(telegram_id, address)
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/delete_address', methods=['POST'])
def delete_address_route(telegram_id):
    data = request.json
    address_id = data.get('address_id')
    delete_user_address(telegram_id, address_id)
    return jsonify({'success': True})

@app.route('/<int:telegram_id>/create_order', methods=['POST'])
def create_order_route(telegram_id):
    data = request.json
    
    order_number = create_order(
        telegram_id=telegram_id,
        delivery_date=data.get('delivery_date'),
        delivery_time=data.get('delivery_time'),
        rental_days=data.get('rental_days'),
        address=data.get('address'),
        preparation_service=data.get('preparation_service', False),
        additional_tobacco=data.get('additional_tobacco', 0)
    )
    
    # Отправляем уведомление администратору через бота
    try:
        from notifications import send_notification_async
        send_notification_async(telegram_id, order_number)
    except Exception as e:
        print(f"Error sending bot notification: {e}")
    
    return jsonify({'success': True, 'order_number': order_number})

@app.route('/<int:telegram_id>/<int:order_number>')
def order_details(telegram_id, order_number):
    order = get_order_details(telegram_id, order_number)
    if not order:
        return "Order not found", 404
    
    user_info = get_user_info(telegram_id)
    
    return render_template('order_details.html', 
                         telegram_id=telegram_id,
                         order=order,
                         user_info=user_info)

@app.route('/<int:telegram_id>/<int:order_number>/adm')
def admin_order_details(telegram_id, order_number):
    order = get_order_details(telegram_id, order_number)
    if not order:
        return "Order not found", 404
    
    user_info = get_user_info(telegram_id)
    
    return render_template('admin_order.html', 
                         telegram_id=telegram_id,
                         order=order,
                         user_info=user_info)

@app.route('/<int:telegram_id>/orders')
def user_orders(telegram_id):
    orders = get_user_orders(telegram_id)
    return jsonify(orders)

@app.route('/<int:telegram_id>/profile')
def user_profile(telegram_id):
    user_data = get_user_info(telegram_id)
    orders = get_user_orders(telegram_id)
    addresses = get_user_addresses(telegram_id)
    
    return render_template('profile.html',
                         telegram_id=telegram_id,
                         user_info=user_data,
                         orders=orders,
                         addresses=addresses)

# WebSocket обработчики
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_user_room')
def handle_join_user_room(telegram_id):
    join_room(f'user_{telegram_id}')
    print(f'User {telegram_id} joined room user_{telegram_id}')

def notify_user_update(telegram_id, event_type, data=None):
    """Отправляет уведомление пользователю через WebSocket"""
    socketio.emit(event_type, data or {}, room=f'user_{telegram_id}')

if __name__ == '__main__':
    init_database()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) 