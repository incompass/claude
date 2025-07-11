// Глобальные переменные
let socket;
let currentHookah = null;
let selectedTariff = null;
let selectedFruit = null;

const fruitPrices = {
    apple: 200,
    orange: 200,
    grapefruit: 250,
    pineapple: 300
};

// Глобальные переменные будут установлены в шаблоне

// Глобальная функция для навигации (для onclick в HTML)
window.showSection = function(section, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    showSectionInternal(section);
};

// Уведомления
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Добавляем комиксные эффекты к сообщениям
    let comicMessage = message;
    if (type === 'success') {
        comicMessage = `🎉 ${message.toUpperCase()}! 🎉`;
    } else if (type === 'error') {
        comicMessage = `💥 ${message.toUpperCase()}! 💥`;
    }
    
    notification.textContent = comicMessage;
    document.body.appendChild(notification);
    
    // Показываем уведомление
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Скрываем уведомление
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Показать лоадер на кнопке
function showButtonLoader(button, originalText) {
    button.disabled = true;
    button.innerHTML = `<span class="loading-spinner mr-2"></span>${originalText}`;
}

// Скрыть лоадер на кнопке
function hideButtonLoader(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// Навигация между секциями
function showSectionInternal(section) {
    console.log('Switching to section:', section);
    
    // Скрываем все секции
    const sections = ['catalog', 'favorites', 'cart', 'profile'];
    sections.forEach(s => {
        const el = document.getElementById(s);
        if (el) {
            el.style.display = 'none';
            el.classList.add('hidden');
        }
    });
    
    // Показываем нужную секцию
    const targetSection = document.getElementById(section);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.remove('hidden');
        console.log('Section shown:', section);
    } else {
        console.error('Section not found:', section);
        return;
    }
    
    // Обновляем активную навигацию
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Находим и активируем нужную кнопку навигации
    const navButtons = document.querySelectorAll('.nav-item');
    navButtons.forEach(button => {
        const dataSection = button.getAttribute('data-section');
        if (dataSection === section) {
            button.classList.add('active');
        }
    });
    
    // Обновляем данные при переходе на секции
    if (section === 'cart') {
        updateCartDisplay();
    } else if (section === 'favorites') {
        updateFavoritesDisplay();
    } else if (section === 'profile') {
        updateProfileDisplay();
    }
}

// Избранное
function toggleFavorite(hookahId) {
    const heartIcons = document.querySelectorAll(`[onclick="toggleFavorite(${hookahId})"]`);
    let wasActive = false;
    
    heartIcons.forEach(heartIcon => {
        if (heartIcon.classList.contains('active')) {
            wasActive = true;
        }
        heartIcon.classList.toggle('active');
        heartIcon.classList.add('heartBeat');
        setTimeout(() => heartIcon.classList.remove('heartBeat'), 600);
    });
    
    fetch(`/${window.telegramId}/toggle_favorite`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hookah_id: hookahId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(wasActive ? 'Удалено из избранного' : 'Добавлено в избранное');
            updateFavoritesDisplay();
            updateFavoriteIcons();
        } else {
            heartIcons.forEach(heartIcon => {
                heartIcon.classList.toggle('active');
            });
            showNotification('Ошибка при обновлении избранного', 'error');
        }
    })
    .catch(error => {
        heartIcons.forEach(heartIcon => {
            heartIcon.classList.toggle('active');
        });
        showNotification('Ошибка при обновлении избранного', 'error');
    });
}

// Модальные окна
function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    document.body.style.overflow = 'auto';
}

function showHookahModal(hookahId) {
    // Получить данные кальяна через API
    fetch(`/${window.telegramId}/get_hookah/${hookahId}`)
        .then(response => response.json())
        .then(hookah => {
            if (!hookah) {
                showNotification('Кальян не найден', 'error');
                return;
            }
            
            // Заполнить модальное окно
            const modalContent = document.getElementById('hookah-details');
            modalContent.innerHTML = `
                <div class="mb-4">
                    <img src="/static/photo/${hookah.name}.jpg" alt="${hookah.name}" class="w-full h-48 object-cover rounded-lg mb-3 border-4 border-black">
                    <h3 class="text-2xl font-bold mb-2 text-purple-600">${hookah.name}</h3>
                    <p class="product-description-modal mb-4">${hookah.description}</p>
                </div>
                
                <div class="mb-4">
                    <h4 class="font-semibold mb-2 text-xl text-purple-600">Выберите тариф:</h4>
                    <div class="space-y-2">
                        <label class="flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="tariff" value="no_tobacco" class="mr-3">
                                <span class="font-black text-lg">Без табака</span>
                            </div>
                            <span class="font-bold text-pink-600 text-xl">${hookah.price_no_tobacco}₽</span>
                        </label>
                        <label class="flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="tariff" value="standard" class="mr-3">
                                <span class="font-black text-lg">Стандарт</span>
                            </div>
                            <span class="font-bold text-pink-600 text-xl">${hookah.price_standard}₽</span>
                        </label>
                        <label class="flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="tariff" value="premium" class="mr-3">
                                <span class="font-black text-lg">Премиум</span>
                            </div>
                            <span class="font-bold text-pink-600 text-xl">${hookah.price_premium}₽</span>
                        </label>
                    </div>
                </div>
                
                <div class="mb-4">
                    <h4 class="font-semibold mb-2 text-xl text-purple-600">Фруктовая чаша:</h4>
                    <div class="space-y-3">
                        <label class="fruit-option flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="fruit" value="" class="mr-3" checked>
                                <span class="font-bold text-lg">Без фрукта</span>
                            </div>
                            <span class="font-bold text-green-600 text-lg">0₽</span>
                        </label>
                        <label class="fruit-option flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="fruit" value="apple" class="mr-3">
                                <span class="font-bold text-lg">🍎 Яблоко</span>
                            </div>
                            <span class="font-bold text-green-600 text-lg">+200₽</span>
                        </label>
                        <label class="fruit-option flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="fruit" value="orange" class="mr-3">
                                <span class="font-bold text-lg">🍊 Апельсин</span>
                            </div>
                            <span class="font-bold text-green-600 text-lg">+250₽</span>
                        </label>
                        <label class="fruit-option flex items-center justify-between p-3 border-4 border-black rounded-lg cursor-pointer">
                            <div class="flex items-center">
                                <input type="radio" name="fruit" value="grapefruit" class="mr-3">
                                <span class="font-bold text-lg">🍋 Грейпфрут</span>
                            </div>
                            <span class="font-bold text-green-600 text-lg">+300₽</span>
                        </label>
                    </div>
                </div>
                
                <button id="add-to-cart-btn" onclick="addToCartFromModal(${hookah.id})" class="w-full btn-primary text-white py-4 rounded-lg font-semibold text-xl">
                    Добавить в корзину
                </button>
            `;
            
            showModal('hookah-modal');
        })
        .catch(error => {
            console.error('Error loading hookah details:', error);
            showNotification('Ошибка загрузки данных кальяна', 'error');
        });
}

function addToCartFromModal(hookahId) {
    const selectedTariff = document.querySelector('input[name="tariff"]:checked');
    if (!selectedTariff) {
        showNotification('Выберите тариф', 'error');
        return;
    }
    
    const selectedFruit = document.querySelector('input[name="fruit"]:checked');
    const fruitBowl = selectedFruit ? selectedFruit.value : '';
    
    addToCart(hookahId, selectedTariff.value, fruitBowl);
}

// Корзина
function addToCart(hookahId, tariff, fruitBowl = null) {
    const button = document.getElementById('add-to-cart-btn');
    const originalText = button.innerHTML;
    showButtonLoader(button, 'Добавляем...');
    
    fetch(`/${window.telegramId}/add_to_cart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            hookah_id: hookahId,
            tariff: tariff,
            fruit_bowl: fruitBowl
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Кальян добавлен в корзину');
            updateCartDisplay();
            hideModal('hookah-modal');
        } else {
            showNotification('Ошибка при добавлении в корзину', 'error');
        }
        hideButtonLoader(button, originalText);
    })
    .catch(error => {
        showNotification('Ошибка при добавлении в корзину', 'error');
        hideButtonLoader(button, originalText);
    });
}

function addDrinkToCart(drinkId, quantity = 1) {
    fetch(`/${window.telegramId}/add_drink_to_cart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            drink_id: drinkId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Напиток добавлен в корзину');
            updateCartDisplay();
            updateDrinkCatalogDisplay();
        } else {
            showNotification('Ошибка при добавлении напитка', 'error');
        }
    })
    .catch(error => {
        showNotification('Ошибка при добавлении напитка', 'error');
    });
}

function updateDrinkInCatalog(drinkId, change) {
    // Получаем текущее количество из корзины
    fetch(`/${window.telegramId}/get_cart`)
        .then(response => response.json())
        .then(cart => {
            const drinkInCart = cart.drinks.find(d => d.drink_id === drinkId);
            const currentQuantity = drinkInCart ? drinkInCart.quantity : 0;
            const newQuantity = currentQuantity + change;
            
            if (newQuantity <= 0) {
                // Удаляем из корзины
                if (drinkInCart) {
                    removeFromCart('drink', drinkInCart.cart_id);
                }
            } else if (currentQuantity === 0) {
                // Добавляем в корзину
                addDrinkToCart(drinkId, 1);
            } else {
                // Обновляем количество
                updateDrinkQuantity(drinkInCart.cart_id, newQuantity);
            }
        });
}

function updateDrinkCatalogDisplay() {
    fetch(`/${window.telegramId}/get_cart`)
        .then(response => response.json())
        .then(cart => {
            // Обновляем отображение всех напитков в каталоге
            document.querySelectorAll('.drink-controls').forEach(control => {
                const drinkId = parseInt(control.dataset.drinkId);
                const drinkInCart = cart.drinks.find(d => d.drink_id === drinkId);
                const quantity = drinkInCart ? drinkInCart.quantity : 0;
                
                const addBtn = control.querySelector('.add-drink-btn');
                const quantityControls = control.querySelector('.quantity-controls');
                const quantityDisplay = control.querySelector('.quantity-display');
                
                if (quantity > 0) {
                    addBtn.classList.add('hidden');
                    quantityControls.classList.remove('hidden');
                    quantityDisplay.textContent = quantity;
                } else {
                    addBtn.classList.remove('hidden');
                    quantityControls.classList.add('hidden');
                }
            });
        });
}

function updateCartDisplay() {
    fetch(`/${window.telegramId}/get_cart`)
        .then(response => response.json())
        .then(cart => {
            const cartContainer = document.getElementById('cart-items');
            if (!cartContainer) return;
            
            cartContainer.innerHTML = '';
            
            let total = 0;
            
            cart.hookahs.forEach((hookah, index) => {
                const itemTotal = hookah.base_price + hookah.fruit_price;
                total += itemTotal;
                
                const item = document.createElement('div');
                item.className = 'bg-white p-4 rounded-lg card-shadow mb-4';
                item.innerHTML = `
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h3 class="font-semibold text-lg">${hookah.name}</h3>
                            <p class="text-sm text-gray-600">Тариф: ${hookah.tariff}</p>
                            ${hookah.fruit_bowl ? `<p class="text-sm text-gray-600">🍎 Фрукт: ${hookah.fruit_bowl}</p>` : ''}
                            <p class="font-semibold text-pink-600 text-lg">${itemTotal}₽</p>
                        </div>
                        <button onclick="removeFromCart('hookah', ${hookah.cart_id})" class="text-red-500 hover:text-red-700 p-2">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                cartContainer.appendChild(item);
            });
            
            cart.drinks.forEach((drink, index) => {
                const itemTotal = drink.price * drink.quantity;
                total += itemTotal;
                
                const item = document.createElement('div');
                item.className = 'bg-white p-4 rounded-lg card-shadow mb-4 bounce-in';
                item.style.animationDelay = `${(cart.hookahs.length + index) * 0.1}s`;
                item.innerHTML = `
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h3 class="font-semibold text-lg">${drink.name}</h3>
                            <p class="text-sm text-gray-600">Количество: ${drink.quantity}</p>
                            <p class="font-semibold text-pink-600 text-lg">${itemTotal}₽</p>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="updateDrinkQuantity(${drink.cart_id}, ${drink.quantity - 1})" class="text-gray-500 hover:text-gray-700 p-1">
                                <i class="fas fa-minus"></i>
                            </button>
                            <span class="px-2">${drink.quantity}</span>
                            <button onclick="updateDrinkQuantity(${drink.cart_id}, ${drink.quantity + 1})" class="text-gray-500 hover:text-gray-700 p-1">
                                <i class="fas fa-plus"></i>
                            </button>
                            <button onclick="removeFromCart('drink', ${drink.cart_id})" class="text-red-500 hover:text-red-700 p-2 ml-2">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                cartContainer.appendChild(item);
            });
            
            const totalElement = document.getElementById('cart-total');
            if (totalElement) {
                totalElement.textContent = `${total}₽`;
                totalElement.classList.add('pulse-animation');
                setTimeout(() => totalElement.classList.remove('pulse-animation'), 1000);
            }
            
            // Показываем/скрываем дополнительные услуги в зависимости от наличия кальянов
            const additionalServices = document.getElementById('additional-services');
            if (additionalServices) {
                if (cart.hookahs.length > 0) {
                    additionalServices.style.display = 'block';
                } else {
                    additionalServices.style.display = 'none';
                }
            }
            
            // Обновляем отображение напитков в каталоге
            updateDrinkCatalogDisplay();
            
            // Обновляем общую сумму с учетом дополнительных услуг
            setTimeout(() => updateCartTotal(), 100);
        });
}

function removeFromCart(type, cartId) {
    fetch(`/${window.telegramId}/remove_from_cart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type: type, cart_id: cartId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Товар удален из корзины');
            updateCartDisplay();
            updateDrinkCatalogDisplay();
        } else {
            showNotification('Ошибка при удалении товара', 'error');
        }
    })
    .catch(error => {
        showNotification('Ошибка при удалении товара', 'error');
    });
}

function updateDrinkQuantity(cartId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart('drink', cartId);
        return;
    }
    
    fetch(`/${window.telegramId}/update_drink_quantity`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cart_id: cartId, quantity: newQuantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay();
            updateDrinkCatalogDisplay();
        } else {
            showNotification('Ошибка при обновлении количества', 'error');
        }
    })
    .catch(error => {
        showNotification('Ошибка при обновлении количества', 'error');
    });
}

function updateFavoritesDisplay() {
    fetch(`/${window.telegramId}/get_favorites`)
        .then(response => response.json())
        .then(favorites => {
            const favoritesContainer = document.getElementById('favorites-content');
            if (!favoritesContainer) return;
            
            favoritesContainer.innerHTML = '';
            
            if (favorites.length === 0) {
                favoritesContainer.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-heart text-6xl text-gray-300 mb-4"></i>
                        <h3 class="text-xl font-semibold text-gray-500 mb-2">Избранное пусто</h3>
                        <p class="text-gray-400">Добавьте кальяны в избранное, чтобы быстро их найти</p>
                    </div>
                `;
                return;
            }
            
            favorites.forEach((hookah, index) => {
                const item = document.createElement('div');
                item.className = 'bg-white rounded-xl card-shadow overflow-hidden';
                item.innerHTML = `
                    <!-- Изображение кальяна -->
                    <div class="relative h-64 overflow-hidden">
                        <img src="/static/photo/${hookah.name}.jpg" alt="${hookah.name}" class="w-full h-full object-cover">
                        <div class="absolute top-4 right-4">
                            <button onclick="toggleFavorite(${hookah.id})" class="heart-icon active text-white hover:scale-110 bg-black bg-opacity-30 rounded-full p-2">
                                <i class="fas fa-heart text-xl"></i>
                            </button>
                        </div>
                    </div>
                    
                    <!-- Информация о кальяне -->
                    <div class="p-4">
                        <h3 class="font-bold text-xl text-gray-800 mb-2">${hookah.name}</h3>
                        <p class="product-description mb-4">${hookah.description}</p>
                        
                        <button onclick="showHookahModal(${hookah.id})" class="w-full btn-primary text-white px-6 py-3 rounded-xl font-semibold">
                            <i class="fas fa-rocket mr-2"></i>ВЫБРАТЬ ТАРИФ!
                        </button>
                    </div>
                `;
                favoritesContainer.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error loading favorites:', error);
        });
}

function updateProfileDisplay() {
    // Обновляем заказы в профиле
    fetch(`/${window.telegramId}/orders`)
        .then(response => response.json())
        .then(orders => {
            const ordersList = document.getElementById('orders-list');
            if (!ordersList) return;
            
            ordersList.innerHTML = '';
            
            if (orders.length === 0) {
                ordersList.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-clipboard-list text-4xl text-gray-300 mb-3"></i>
                        <p class="text-gray-500">У вас пока нет заказов</p>
                    </div>
                `;
                return;
            }
            
            orders.forEach((order, index) => {
                const orderElement = document.createElement('div');
                orderElement.className = 'p-4 border rounded-lg mb-3';
                orderElement.innerHTML = `
                    <div class="flex justify-between items-center">
                        <div>
                            <div class="font-semibold">Заказ #${order.order_number}</div>
                            <div class="text-sm text-gray-600">${order.delivery_date} в ${order.delivery_time}</div>
                            <div class="text-sm text-gray-600">Статус: <span class="font-medium">${order.status}</span></div>
                        </div>
                        <div class="text-right">
                                                         <div class="font-semibold text-pink-600">${order.total_price}₽</div>
                            <a href="/${window.telegramId}/${order.order_number}" class="text-blue-500 text-sm hover:underline">Подробнее</a>
                        </div>
                    </div>
                `;
                ordersList.appendChild(orderElement);
            });
        })
        .catch(error => {
            console.error('Error loading orders:', error);
        });
}

// WebSocket для обновлений в реальном времени
function initWebSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('WebSocket connected');
            socket.emit('join_user_room', window.telegramId);
        });
        
        socket.on('disconnect', function() {
            console.log('WebSocket disconnected');
        });
        
        socket.on('cart_updated', function(data) {
            console.log('Cart updated via WebSocket');
            updateCartDisplay();
            showNotification('Корзина обновлена');
        });
        
        socket.on('favorites_updated', function(data) {
            console.log('Favorites updated via WebSocket');
            updateFavoritesDisplay();
            showNotification('Избранное обновлено');
        });
        
        socket.on('order_status_updated', function(data) {
            console.log('Order status updated:', data);
            showNotification(`Статус заказа #${data.order_number} изменен: ${data.status}`);
            if (typeof updateProfileDisplay === 'function') {
                updateProfileDisplay();
            }
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Показываем каталог по умолчанию
    document.getElementById('catalog').style.display = 'block';
    document.getElementById('catalog').classList.remove('hidden');
    
    updateCartDisplay();
    updateDrinkCatalogDisplay();
    updateFavoriteIcons();
    initWebSocket();
    
    // Добавляем обработчики для навигации
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const section = this.getAttribute('data-section');
            if (section) {
                showSectionInternal(section);
            }
        });
    });
    
    // Убираем анимации
});

// Обновляем иконки избранного в каталоге
function updateFavoriteIcons() {
    fetch(`/${window.telegramId}/get_favorites`)
        .then(response => response.json())
        .then(favorites => {
            const favoriteIds = favorites.map(f => f.id);
            
            document.querySelectorAll('.heart-icon').forEach(icon => {
                const onclick = icon.getAttribute('onclick');
                if (onclick) {
                    const match = onclick.match(/toggleFavorite\((\d+)\)/);
                    if (match) {
                        const hookahId = parseInt(match[1]);
                        if (favoriteIds.includes(hookahId)) {
                            icon.classList.add('active');
                        } else {
                            icon.classList.remove('active');
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading favorites:', error);
        });
}

// Закрытие модальных окон
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        hideModal(e.target.id);
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            hideModal(modal.id);
        });
    }
});

// Оформление заказа
function proceedToCheckout() {
    // Проверяем, есть ли товары в корзине
    fetch(`/${window.telegramId}/get_cart`)
        .then(response => response.json())
        .then(cart => {
            if (cart.hookahs.length === 0 && cart.drinks.length === 0) {
                showNotification('Корзина пуста. Добавьте товары для оформления заказа.', 'error');
                return;
            }
            
            // Показываем модальное окно оформления заказа
            showCheckoutModal();
        })
        .catch(error => {
            showNotification('Ошибка при проверке корзины', 'error');
        });
}

function showCheckoutModal() {
    // Создаем модальное окно для оформления заказа
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content max-w-md mx-auto">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">Оформление заказа</h2>
                <button onclick="hideCheckoutModal()" class="text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Дата доставки</label>
                    <input type="date" id="delivery-date" class="w-full p-2 border rounded-lg" required>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Время доставки</label>
                    <input type="time" id="delivery-time" class="w-full p-2 border rounded-lg" required>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Дни аренды</label>
                    <input type="number" id="rental-days" min="1" value="1" class="w-full p-2 border rounded-lg" required>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Адрес доставки</label>
                    <input type="text" id="delivery-address" placeholder="Введите адрес" class="w-full p-2 border rounded-lg" required>
                </div>
                
                <button onclick="submitOrder()" class="w-full btn-primary text-white py-3 rounded-lg font-semibold">
                    Оформить заказ
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Устанавливаем минимальную дату на сегодня
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('delivery-date').min = today;
}

function hideCheckoutModal() {
    const modal = document.querySelector('.modal.active');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

function submitOrder() {
    const deliveryDate = document.getElementById('delivery-date').value;
    const deliveryTime = document.getElementById('delivery-time').value;
    const rentalDays = document.getElementById('rental-days').value;
    const address = document.getElementById('delivery-address').value;
    
    if (!deliveryDate || !deliveryTime || !rentalDays || !address) {
        showNotification('Заполните все поля', 'error');
        return;
    }
    
    const preparationService = document.getElementById('preparation-service')?.checked || false;
    const additionalTobacco = parseInt(document.getElementById('additional-tobacco')?.value || '0');
    
    const orderData = {
        delivery_date: deliveryDate,
        delivery_time: deliveryTime,
        rental_days: parseInt(rentalDays),
        address: address,
        preparation_service: preparationService,
        additional_tobacco: additionalTobacco
    };
    
    fetch(`/${window.telegramId}/create_order`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Заказ успешно оформлен');
            hideCheckoutModal();
            updateCartDisplay();
            // Переходим на страницу заказа
            window.location.href = `/${window.telegramId}/${data.order_number}`;
        } else {
            showNotification('Ошибка при оформлении заказа', 'error');
        }
    })
    .catch(error => {
        showNotification('Ошибка при оформлении заказа', 'error');
    });
}

// Управление количеством табака
function updateTobaccoQuantity(change) {
    const quantityElement = document.getElementById('tobacco-quantity');
    const totalElement = document.getElementById('tobacco-total');
    
    if (!quantityElement || !totalElement) return;
    
    let currentQuantity = parseInt(quantityElement.textContent) || 0;
    let newQuantity = currentQuantity + change;
    
    // Не позволяем количеству быть меньше 0
    if (newQuantity < 0) newQuantity = 0;
    
    quantityElement.textContent = newQuantity;
    totalElement.textContent = `${newQuantity * 350}₽`;
    
    // Обновляем скрытое поле для отправки формы
    let hiddenInput = document.getElementById('additional-tobacco');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = 'additional-tobacco';
        document.body.appendChild(hiddenInput);
    }
    hiddenInput.value = newQuantity;
    
    // Обновляем общую сумму корзины
    updateCartTotal();
}

// Обновляем общую сумму корзины с учетом дополнительных услуг
function updateCartTotal() {
    fetch(`/${window.telegramId}/get_cart`)
        .then(response => response.json())
        .then(cart => {
            let total = 0;
            
            // Считаем кальяны
            cart.hookahs.forEach(hookah => {
                total += hookah.base_price + hookah.fruit_price;
            });
            
            // Считаем напитки
            cart.drinks.forEach(drink => {
                total += drink.price * drink.quantity;
            });
            
            // Добавляем дополнительные услуги
            const preparationService = document.getElementById('preparation-service')?.checked || false;
            if (preparationService) {
                total += 290;
            }
            
            const additionalTobacco = parseInt(document.getElementById('tobacco-quantity')?.textContent || '0');
            total += additionalTobacco * 350;
            
            // Обновляем отображение
            const totalElement = document.getElementById('cart-total');
            if (totalElement) {
                totalElement.textContent = `${total}₽`;
            }
        });
}

// Обновляем сумму при изменении чекбокса приготовки
document.addEventListener('change', function(e) {
    if (e.target.id === 'preparation-service') {
        updateCartTotal();
    }
}); 