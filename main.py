import os
import threading
import time
from app import app, socketio
from database import init_database

def run_flask():
    try:
        init_database()
        print("Starting Flask app with SocketIO...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        # Fallback to regular Flask if SocketIO fails
        print("Falling back to regular Flask...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    
def run_bot():
    time.sleep(2)  # Даем Flask время запуститься
    from bot import main
    main()

if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота в основном потоке
    run_bot() 