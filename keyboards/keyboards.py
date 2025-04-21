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

    # Разбиваем категории на 4 строки
    row_width = 4
    rows = [categories[i:i + row_width] for i in range(0, len(categories), row_width)]

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])

    # Добавляем кнопки в строки
    for row in rows:
        keyboard.keyboard.append([KeyboardButton(text=name) for _, name in row])

    # Добавляем кнопку "Назад"
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


def get_delivery_type_markup():
    delivery_types = get_delivery_types()  # Получаем все типы доставки
    if delivery_types:
        keyboard = InlineKeyboardMarkup(
            row_width=2,
            inline_keyboard=[
                [InlineKeyboardButton(text=delivery_types['delivery_type'], callback_data=f"delivery_type_{delivery_types['id_type']}")]
                for delivery_type in (delivery_types,
                                      [InlineKeyboardButton(text="Назад", callback_data="nav_menu()")])
            ]
        )
        return keyboard
    else:
        return None


def delivery_time_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text="Как можно скорее", callback_data="delivery_time:ASAP")],
        [InlineKeyboardButton(text="К определенному времени", callback_data="delivery_time:scheduled")]
    ])
    buttons = [

    ]
    keyboard.add(*buttons)
    return keyboard

def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить новый товар"), KeyboardButton(text="Удалить товар")],
            [KeyboardButton(text="Посмотреть заказы")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

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
            [InlineKeyboardButton(text="🛒 ПОМЕНЯТЬ ТУТ БУКАВЫ", callback_data=f"order_{product_id}")]
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
            [InlineKeyboardButton(text="Оформить заказ", callback_data=f"process_order_{order_id}")]
        ]
    )