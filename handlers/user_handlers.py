from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext

from keyboards.keyboards import nav_keyboard, categories_keyboard, get_product_inline_markup, get_delivery_type_markup, \
    delivery_time_keyboard, get_cart_item_markup
from db.db_utils import get_user, register_user, get_category_by_name, get_products_by_category, get_order_history, \
    get_order_items, get_order_status, create_order, get_product_details, get_delivery_types, add_to_cart, \
    get_cart_items, remove_cart_item, update_cart_item_quantity
from states.states import Registration, Order
from aiogram.filters import Command, StateFilter


async def start_command(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer("Привет! Рад видеть вас снова в 5 Вкусов! Используйте /nav для навигации.",
                             reply_markup=nav_keyboard())
    else:
        await message.answer(
            "Привет! Похоже, вы впервые здесь. Пожалуйста, пройдите регистрацию, чтобы пользоваться ботом.")
        await state.set_state(Registration.waiting_for_name)
        await message.answer("Введите ваше имя:")


async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(Registration.waiting_for_phone)
    await message.answer("Введите ваш номер телефона:")


async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    name = data['name']
    phone = data['phone']
    tg_user_id = message.from_user.id

    if register_user(name, phone, tg_user_id):
        await message.answer("Регистрация прошла успешно!", reply_markup=nav_keyboard())
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")

    await state.clear()


async def nav_command(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=nav_keyboard())


async def profile_command(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        profile_text = f"Ваш профиль:\nИмя: {user['name']}\nТелефон: {user['phone']}\nID: {user['tg_user_id']}"
        await message.answer(profile_text)
    else:
        await message.answer("Пожалуйста, зарегистрируйтесь, чтобы просмотреть профиль. Используйте /start.")


async def view_menu(message: types.Message):
    keyboard = categories_keyboard()
    if keyboard:
        await message.answer("Выберите категорию:", reply_markup=keyboard)
    else:
        await message.answer("Не удалось загрузить категории меню.")


async def process_category(message: types.Message):
    category_name = message.text.strip()

    if category_name == "Назад":
        await message.answer("Вы вернулись в главное меню.")
        return

    category = get_category_by_name(category_name)
    if category is None:
        await message.answer("Категория не найдена.")
        return

    products = get_products_by_category(category['id_category'])

    if products:
        text = "\n\n".join([f"{p['name']} — {p['price']}₽" for p in products])
    else:
        text = "В этой категории пока нет товаров."

    await message.answer(text)


async def process_add_to_cart(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split(':')[1]
    quantity = 1

    if add_to_cart(callback_query.from_user.id, product_id, quantity):
        await callback_query.answer("Товар добавлен в корзину!", show_alert=True)
    else:
        await callback_query.answer("Не удалось добавить товар в корзину.", show_alert=True)


async def view_order_history(message: types.Message):
    tg_user_id = message.from_user.id
    orders = get_order_history(tg_user_id)

    if orders:
        text = "Ваша история заказов:\n"
        for order in orders:
            order_items = get_order_items(order['id_orders'])
            items_text = ""
            total_sum = 0

            for item in order_items:
                product_details = get_product_details(item['id_product'])
                if product_details:
                    items_text += f"- {product_details['name']} x {item['quantity']} ({item['price_to_quan']} руб.)\n"
                    total_sum += float(item['price_to_quan'])
                else:
                    items_text += f"- Product ID: {item['id_product']} x {item['quantity']} (Цена неизвестна)\n"

            text += f"""
Заказ №{order['id_orders']}
Дата: {order['date']}
Состав заказа:
{items_text}
Сумма: {order['summa']} руб.
Тип доставки: {order['delivery_type']}
------------------------
"""
        await message.answer(text)
    else:
        await message.answer("У вас пока нет заказов.")


async def view_order_status(message: types.Message):
    tg_user_id = message.from_user.id
    status = get_order_status(tg_user_id)

    if status:
        await message.answer(f"Статус вашего заказа: {status}")
    else:
        await message.answer("Нет активных заказов.")


async def view_cart(message: types.Message):
    tg_user_id = message.from_user.id
    cart_items = get_cart_items(tg_user_id)

    if cart_items:
        total_amount = 0
        cart_text = "Ваша корзина:\n"
        for item in cart_items:
            cart_text += f"- {item['product_name']} x {item['quantity']} ({item['product_price'] * item['quantity']} руб.)\n"
            total_amount += item['product_price'] * item['quantity']

        cart_text += f"\nОбщая сумма: {total_amount} руб."
        await message.answer(cart_text)

        for item in cart_items:
            markup = get_cart_item_markup(item['id_basket'])
            await message.answer(f"Действия для: {item['product_name']}", reply_markup=markup)

        checkout_kb = types.InlineKeyboardMarkup()
        checkout_kb.add(types.InlineKeyboardButton(text="Оформить заказ", callback_data="checkout"))
        await message.answer("Что вы хотите сделать?", reply_markup=checkout_kb)
    else:
        await message.answer("Ваша корзина пуста.")


async def update_quantity_callback(callback_query: types.CallbackQuery, state: FSMContext):
    cart_item_id = callback_query.data.split(':')[1]
    await state.update_data(cart_item_id=cart_item_id)
    await Order.waiting_for_quantity.set()
    await callback_query.message.answer("Введите новое количество:")
    await callback_query.answer()


async def process_new_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer("Пожалуйста, введите положительное число.")
            return

        state_data = await state.get_data()
        cart_item_id = state_data.get('cart_item_id')
        if update_cart_item_quantity(cart_item_id, quantity):
            await message.answer("Количество товара в корзине обновлено.")
        else:
            await message.answer("Не удалось обновить количество товара.")

        await state.clear()
        await view_cart(message)
    except ValueError:
        await message.answer("Неверный формат количества. Введите целое число.")


async def remove_from_cart_callback(callback_query: types.CallbackQuery):
    cart_item_id = callback_query.data.split(':')[1]
    if remove_cart_item(cart_item_id):
        await callback_query.message.answer("Товар удален из корзины.")
    else:
        await callback_query.message.answer("Не удалось удалить товар из корзины.")
    await callback_query.answer()
    await view_cart(callback_query.message)


async def process_checkout(callback_query: types.CallbackQuery):
    tg_user_id = callback_query.from_user.id
    cart_items = get_cart_items(tg_user_id)

    if not cart_items:
        await callback_query.answer("Ваша корзина пуста! Нечего оформлять.", show_alert=True)
        return

    await Order.choosing_delivery_type.set()
    await callback_query.message.answer("Выберите тип доставки:", reply_markup=get_delivery_type_markup())
    await callback_query.answer()


async def process_delivery_type(callback_query: types.CallbackQuery, state: FSMContext):
    delivery_type_id = callback_query.data.split(':')[1]
    await state.update_data(delivery_type_id=delivery_type_id)
    delivery_type_info = get_delivery_types()
    delivery_info = next((item for item in delivery_type_info if item['id_type'] == int(delivery_type_id)), None)
    if delivery_info:
        await state.update_data(delivery_type=delivery_info['delivery_type'])
        if delivery_info['delivery_type'] == "Доставка":
            await Order.waiting_for_address.set()
            await callback_query.message.answer("Пожалуйста, отправьте адрес доставки:")
        elif delivery_info['delivery_type'] == "Самовывоз":
            await Order.choosing_delivery_time.set()
            await callback_query.message.answer("Выберите время самовывоза:", reply_markup=delivery_time_keyboard())
    else:
        await callback_query.answer("Ошибка получения информации о доставке.")

    await callback_query.answer()


async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    await Order.choosing_delivery_time.set()
    await message.answer("Выберите время доставки:", reply_markup=delivery_time_keyboard())


async def process_delivery_time(callback_query: types.CallbackQuery, state: FSMContext):
    delivery_time = callback_query.data.split(':')[1]
    await state.update_data(delivery_time=delivery_time)
    await Order.accepting_data_processing.set()
    await callback_query.message.answer(
        "Для завершения оформления заказа необходимо согласие на обработку персональных данных.")
    await callback_query.message.answer("Подтвердите свое согласие, отправив '+'.")
    await callback_query.answer()


async def process_data_processing(message: types.Message, state: FSMContext):
    await state.update_data(data_processing_accepted=True)

    data = await state.get_data()
    delivery_type_id = data.get('delivery_type_id')
    delivery_address = data.get('delivery_address', "")
    delivery_time = data['delivery_time']
    tg_user_id = message.from_user.id

    cart_items = get_cart_items(tg_user_id)

    if not cart_items:
        await message.answer("Ваша корзина пуста.")
        await state.clear()
        return

    total_amount = sum(item['product_price'] * item['quantity'] for item in cart_items)

    product_ids_quantities = {item['id_product']: item['quantity'] for item in cart_items}
    order_id = create_order(tg_user_id, delivery_type_id, delivery_address, delivery_time, total_amount,
                            product_ids_quantities)

    if order_id:
        await message.answer(f"Заказ успешно оформлен! Номер вашего заказа: {order_id}")

    else:
        await message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.")

    await state.clear()


def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(nav_command, Command("nav"))
    dp.message.register(profile_command, Command("profile"))

    dp.message.register(process_name, StateFilter(Registration.waiting_for_name))
    dp.message.register(process_phone, StateFilter(Registration.waiting_for_phone))

    dp.message.register(view_menu, F.text == "Просмотр меню")
    dp.message.register(process_category, F.text != "Назад")
    dp.callback_query.register(process_add_to_cart, F.data.startswith("add_to_cart:"))

    dp.message.register(view_order_history, F.text == "История заказов")
    dp.message.register(view_order_status, F.text == "Статус заказа")
    dp.message.register(view_cart, F.text == "Корзина")

    dp.callback_query.register(update_quantity_callback, F.data.startswith("update_quantity:"), F.state.any())
    dp.message.register(process_new_quantity, F.state == Order.waiting_for_quantity)
    dp.callback_query.register(remove_from_cart_callback, F.data.startswith("remove_from_cart:"))

    dp.callback_query.register(process_checkout, F.data == "checkout")
    dp.message.register(nav_command, F.text == "Назад")
