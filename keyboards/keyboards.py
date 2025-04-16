

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db.db_utils import get_menu_categories, get_delivery_types

# Навигационное меню
def nav_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=[
        [KeyboardButton(text="Просмотр меню")],
        [KeyboardButton(text="История заказов")],
        [KeyboardButton(text="Статус заказа")],
        [KeyboardButton(text="Корзина")]
    ])
    return keyboard

def categories_keyboard():
    categories = get_menu_categories()

    if not categories:
        return None

    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2,
        keyboard=[
            [KeyboardButton(text=name)]
            for cat_id, name in categories
        ]
    )

    keyboard.keyboard.append([KeyboardButton(text="Назад")])
    return keyboard

def get_delivery_type_markup():
    delivery_types = get_delivery_types()  # Получаем все типы доставки
    if delivery_types:
        keyboard = InlineKeyboardMarkup(
            row_width=2,
            inline_keyboard=[
                [InlineKeyboardButton(text=delivery_type['delivery_type'], callback_data=f"delivery_type:{delivery_type['id_type']}")]
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

def product_delete_keyboard(product_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Удалить", callback_data=f"delete_product:{product_id}"))
    return keyboard

def get_product_inline_markup(products):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        keyboard.add(InlineKeyboardButton(text=f"Добавить {product['name']} в корзину", callback_data=f"add_to_cart:{product['id_product']}"))
    return keyboard

def get_cart_item_markup(cart_item_id):
   markup = InlineKeyboardMarkup()
   markup.add(InlineKeyboardButton("Изменить количество", callback_data=f"update_quantity:{cart_item_id}"))
   markup.add(InlineKeyboardButton("Удалить из корзины", callback_data=f"remove_from_cart:{cart_item_id}"))
   return markup