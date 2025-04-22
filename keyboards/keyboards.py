import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from db.db_utils import get_menu_categories, get_delivery_types, get_products_by_category_as_menu


# Навигационное меню
def nav_keyboard(is_admin=False):
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Просмотр меню")],
        [KeyboardButton(text="История заказов")],
        [KeyboardButton(text="Статус заказа")],
        [KeyboardButton(text="Корзина")]
    ])

    if is_admin:
        keyboard.keyboard.append([KeyboardButton(text="Админ-панель")])

    return keyboard

def categories_keyboard():
    categories = get_menu_categories()

    if not categories:
        return None

    row_width = 4
    rows = [categories[i:i + row_width] for i in range(0, len(categories), row_width)]

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])

    for row in rows:
        keyboard.keyboard.append([KeyboardButton(text=name) for _, name in row])

    keyboard.keyboard.append([KeyboardButton(text="Назад")])

    return keyboard

def get_deletion_keyboard(category_id):
    products = get_products_by_category_as_menu(category_id)
    logging.info(f"products: {products}")

    # Количество кнопок в строке
    row_width = 2
    rows = [products[i:i + row_width] for i in range(0, len(products), row_width)]

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])

    # Добавляем кнопки: по 2 в строку
    for row in rows:
        keyboard.keyboard.append([KeyboardButton(text=item["name"]) for item in row])

    # Кнопка "Назад" — отдельной строкой
    keyboard.keyboard.append([KeyboardButton(text="Назад")])

    return keyboard


# def get_delivery_type_markup():
#     delivery_types = get_delivery_types()  # Получаем все типы доставки
#     if delivery_types:
#         keyboard = InlineKeyboardMarkup(
#             row_width=2,
#             inline_keyboard=[
#                 [InlineKeyboardButton(text=delivery_types['delivery_type'], callback_data=f"delivery_type_{delivery_types['id_type']}")]
#                 for delivery_type in (delivery_types,
#                                       [InlineKeyboardButton(text="Назад", callback_data="nav_menu()")])
#             ]
#         )
#         return keyboard
#     else:
#         return None

def get_delivery_type_markup():
    delivery_types = get_delivery_types()  # Ожидается список словарей [{'id_type': ..., 'delivery_type': ...}, ...]

    if delivery_types:
        # Первый ряд — два типа доставки
        buttons_row_1 = [
            InlineKeyboardButton(
                text=dt['name'],
                callback_data=f"delivery_type_{dt['id_type']}"
            ) for dt in delivery_types
        ]

        # Второй ряд — кнопка "Назад"
        buttons_row_2 = [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cart")
        ]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[buttons_row_1, buttons_row_2]
        )
        return keyboard
    else:
        return None


def delivery_time_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text="Как можно скорее", callback_data="delivery_time_ASAP")],
        [InlineKeyboardButton(text="К определенному времени", callback_data="delivery_time_scheduled")]
    ])
    return keyboard

def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить новый товар"), KeyboardButton(text="Удалить товар")],
            [KeyboardButton(text="Посмотреть заказы"), KeyboardButton(text="Изменить статус заказа")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    statuses = ["Оформлен", "Готовится", "Передан в доставку", "Готов", "Завершен"]

    keyboard = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=status, callback_data=f"update_status_{order_id}_{status}")] for status in statuses
    ])
    return keyboard

# def product_delete_keyboard(product_id):
#     keyboard = InlineKeyboardMarkup()
#     keyboard.add(InlineKeyboardButton("Удалить", callback_data=f"delete_product:{product_id}"))
#     return keyboard

def get_product_inline_markup(products):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        keyboard.add(InlineKeyboardButton(text=f"Добавить {product['name']} в корзину", callback_data=f"add_to_cart:{product['id_product']}"))
    return keyboard

# def get_cart_item_markup(cart_item_id):
#    markup = InlineKeyboardMarkup()
#    markup.add(InlineKeyboardButton("Изменить количество", callback_data=f"update_quantity:{cart_item_id}"))
#    markup.add(InlineKeyboardButton("Удалить из корзины", callback_data=f"remove_from_cart:{cart_item_id}"))
#    return markup

def add_select_button(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"order_{product_id}")]
        ]
    )

def add_cancel_select_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_select")]
        ]
    )

def add_order_button(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data=f"process_order_{order_id}")],
            [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_cart_{order_id}")]
        ]
    )

def generate_edit_cart_keyboard(cart_items) -> InlineKeyboardMarkup:
    keyboard = []
    for item in cart_items:
        button_text = f"{item['product_name']} (x{item['quantity']})"
        callback_data = f"edit_item_{item['id_product']}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_cart")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def generate_edit_actions_keyboard(product_id) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Изменить количество", callback_data=f"edit_quantity_{product_id}")],
        [InlineKeyboardButton(text="Удалить из корзины", callback_data=f"remove_from_cart_{product_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_cart")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def add_accept_data_processing_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data="accept_data_processing")]
        ]
    )