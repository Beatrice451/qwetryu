import os
import re
from datetime import datetime

from aiogram import types, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardMarkup

from db.db_utils import get_user, register_user, get_category_by_name, get_products_by_category, get_order_history, \
    get_order_items, get_order_status, update_order, get_product_details, get_delivery_types, add_to_cart, \
    get_cart_items, update_cart_item_quantity, get_menu_categories, get_delivery_price, remove_item_from_cart
from keyboards.keyboards import nav_keyboard, categories_keyboard, get_delivery_type_markup, \
    delivery_time_keyboard, add_select_button, add_cancel_select_button, add_order_button, \
    add_accept_data_processing_button, generate_edit_cart_keyboard, generate_edit_actions_keyboard
from states.states import Registration, Order, Admin
from utils.utils import is_admin, delete_saved_messages

category_names = [i[1] for i in get_menu_categories()]


async def start_command(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer("Привет! Рад видеть вас снова в 5 Вкусов! Используйте /nav для навигации.",
                             reply_markup=nav_keyboard())
    else:
        await message.answer(
            "Привет! Похоже, вы впервые здесь. Пожалуйста, пройдите регистрацию, чтобы пользоваться ботом.",
            reply_markup=types.ReplyKeyboardRemove())
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
    if not re.fullmatch(r'^\+7\d{10}$', phone):
        await message.answer("❌ Некорректный номер. Формат: +7XXXXXXXXXX (11 цифр, например: +79995554433)")
        return
    tg_user_id = message.from_user.id

    if register_user(name, phone, tg_user_id):
        await message.answer("Регистрация прошла успешно!", reply_markup=nav_keyboard())
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")

    await state.clear()


async def nav_command(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, зарегистрируйтесь, чтобы просмотреть меню. Используйте /start.")
        return
    await message.answer("Выберите действие:", reply_markup=nav_keyboard(is_admin=is_admin(message.from_user.id)))


async def profile_command(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        profile_text = f"Ваш профиль:\nИмя: {user['name']}\nТелефон: {user['phone']}\nID: {user['tg_user_id']}"
        await message.answer(profile_text)
    else:
        await message.answer("Пожалуйста, зарегистрируйтесь, чтобы просмотреть профиль. Используйте /start.")


async def view_menu(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        keyboard = categories_keyboard()
        await message.answer("Выберите категорию:", reply_markup=keyboard)
    else:
        await message.answer("Пожалуйста, зарегистрируйтесь, чтобы просмотреть меню. Используйте /start.")


async def process_category(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, зарегистрируйтесь, чтобы просмотреть меню. Используйте /start.")
        return
    category_name = message.text.strip()

    if category_name == "Назад":
        await message.answer("Вы вернулись в главное меню.")
        return

    category = get_category_by_name(category_name)
    if category is None:
        await message.answer("Категория не найдена.")
        return

    products = get_products_by_category(category['id_category'])

    if not products:
        await message.answer("В этой категории пока нет товаров.")
        return

    for product in products:
        name = product['name']
        description = product.get('descript', 'Описание отсутствует.')
        price = product['price']
        photo = product['photo']
        photo_path = "resources/images/" + product['photo']

        caption = (
            f"<b>Название:</b> {name}\n\n"
            f"<b>Описание:</b> {description}\n\n"
            f"<b>Цена:</b> {price}₽"
        )

        # Проверим наличие файла
        if not os.path.exists(photo_path) or not photo:
            await message.answer(
                "<b>Странно, но фото нет...</b>\n\n" +
                caption,
                parse_mode="HTML",
                reply_markup=add_select_button(product['id_product'])
            )
            continue

        photo = FSInputFile(photo_path)

        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML",
                                   reply_markup=add_select_button(product['id_product']))


async def process_select_product(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split('_')[1]
    await state.set_state(Order.waiting_for_quantity)

    msg = await callback_query.message.answer("Выберите количество:", reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(
        product_id=product_id,
        message_id=msg.message_id,
        inline_msg=callback_query.message.message_id
    )

    await callback_query.message.edit_reply_markup(
        reply_markup=add_cancel_select_button()
    )


async def process_cancel_select(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Выбор отменен.")

    data = await state.get_data()
    msg_id = data.get('message_id')
    await callback_query.message.edit_reply_markup(
        reply_markup=add_select_button(data.get('product_id'))
    )

    if msg_id:
        try:
            await callback_query.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=msg_id
            )
        except Exception:
            pass
        await delete_saved_messages(callback_query.bot, callback_query.message.chat.id, state)

    await state.clear()


async def process_quantity(message: types.Message, state: FSMContext):
    msg = message.text
    if not msg.isdigit() or int(msg) <= 0:
        await message.answer("Пожалуйста, введите корректное количество!")
        return
    quantity = int(msg)

    data = await state.get_data()
    product_id = data.get('product_id')

    if quantity <= 0:
        await message.answer("Количество товара должно быть больше 0.")
        return

    msg_id = data.get('message_id')
    if msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    from main import bot
    inline_id = data.get('inline_msg')
    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=inline_id,
        reply_markup=add_select_button(product_id)
    )
    if add_to_cart(message.from_user.id, product_id, quantity):
        # бот импортируется посреди кода, потому что иначе начнётся циклический импорт и всё упадёт
        await state.clear()
        await message.answer("Товар добавлен в корзину!\nКоличество: " + str(quantity),
                             reply_markup=categories_keyboard())
    else:
        await state.clear()
        await message.answer("Не удалось добавить товар в корзину.")


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
Дата: {order['deliv_date']}
Состав заказа:
{items_text}
Сумма: {order['summa']} руб.
Тип доставки: {order['name']}
------------------------
"""
        await message.answer(text)
    else:
        await message.answer("У вас пока нет заказов.")


async def view_order_status(message: types.Message):
    tg_user_id = message.from_user.id
    order_info = get_order_status(tg_user_id)
    if order_info:
        status, deliv_dt = order_info
        formatted_date = deliv_dt.strftime("%d/%m/%Y %H:%M")
        await message.answer(f"Статус вашего последнего заказа: {status}\nДата оформления: {formatted_date}")
    else:
        await message.answer("У вас пока нет заказов.")


async def view_cart(message: types.Message, state: FSMContext):
    tg_user_id = message.from_user.id
    cart_items = get_cart_items(tg_user_id)

    if cart_items:
        total_amount = 0
        cart_text = "Ваша корзина:\n"
        for item in cart_items:
            cart_text += f"- {item['product_name']} x {item['quantity']} ({item['product_price'] * item['quantity']} руб.)\n"
            total_amount += item['product_price'] * item['quantity']

        delivery_price = get_delivery_price(2)
        print(delivery_price)
        cart_text += f"\nДоставка: {0 if total_amount > 1000 else delivery_price} руб."
        cart_text += f"\n\nОбщая сумма: {total_amount if total_amount > 1000 else total_amount + delivery_price} руб."

        msg = await message.answer(cart_text, reply_markup=add_order_button(tg_user_id))
        await state.update_data(
            msg_id=message.message_id,
            cart_text=cart_text,
            message_cart=msg.message_id
        )
    else:
        await message.answer("Ваша корзина пуста.")


async def update_quantity_callback(callback_query: types.CallbackQuery, state: FSMContext):
    cart_item_id = callback_query.data.split('_')[-1]
    await state.update_data(cart_item_id=cart_item_id)
    await state.set_state(Order.waiting_for_new_quantity)
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
        print(cart_item_id, quantity, message.from_user.id)
        if update_cart_item_quantity(message.from_user.id, cart_item_id, quantity):
            await message.answer("Количество товара в корзине обновлено.")
        else:
            await message.answer("Не удалось обновить количество товара.")

        await state.clear()
        await view_cart(message, state)
    except ValueError:
        await message.answer("Неверный формат количества. Введите целое число.")


async def edit_cart(callback_query: types.CallbackQuery, state: FSMContext):
    tg_user_id = callback_query.from_user.id
    cart_items = get_cart_items(tg_user_id)

    if not cart_items:
        await callback_query.answer("Ваша корзина пуста! Нечего редактировать.")
        return

    await state.update_data(cart_text=callback_query.message.text)
    edit_text = callback_query.message.text + "\n\nВыберите товар для редактирования:"
    keyboard = generate_edit_cart_keyboard(cart_items)

    await callback_query.message.edit_text(edit_text, reply_markup=keyboard)
    await state.set_state(Order.editing_cart)


async def back_to_cart(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart_text = data.get('cart_text')
    await callback_query.message.edit_text(
        text=cart_text,
        reply_markup=add_order_button(callback_query.from_user.id)
    )


async def process_checkout(callback_query: types.CallbackQuery, state: FSMContext):
    tg_user_id = callback_query.from_user.id
    cart_items = get_cart_items(tg_user_id)

    if not cart_items:
        await callback_query.answer("Ваша корзина пуста! Нечего оформлять.")
        return
    data = await state.get_data()
    cart_text = data['cart_text']
    await state.set_state(Order.choosing_delivery_type)
    await callback_query.message.edit_text(
        text=f"{cart_text}\n\nВыберите тип доставки:",
        reply_markup=get_delivery_type_markup()
    )
    await callback_query.answer()


async def process_delivery_type(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    messages_for_deletion = data.get("messages_for_deletion", [])
    delivery_type_id = callback_query.data.split('_')[-1]
    await state.update_data(delivery_type_id=delivery_type_id)
    delivery_type_info = get_delivery_types()
    delivery_info = next((item for item in delivery_type_info if item['id_type'] == int(delivery_type_id)), None)
    if delivery_info:
        await state.update_data(delivery_type=delivery_info['name'])
        if delivery_info['name'] == "Доставка":
            await state.set_state(Order.waiting_for_address)
            msg = await callback_query.message.answer("Пожалуйста, отправьте адрес доставки:")
            messages_for_deletion.append(msg.message_id)
            await state.update_data(
                messages_for_deletion=messages_for_deletion
            )
        elif delivery_info['name'] == "Самовывоз":
            await state.set_state(Order.choosing_delivery_time)
            new_msg = await callback_query.message.answer("Выберите время самовывоза:",
                                                          reply_markup=delivery_time_keyboard())
            messages_for_deletion.append(new_msg.message_id)
            await state.update_data(messages_for_deletion=messages_for_deletion)
            print("samovsvoz added for deletion: ", new_msg.message_id)
    else:
        await callback_query.answer("Ошибка получения информации о доставке.")

    await callback_query.answer()


async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    await state.set_state(Order.choosing_delivery_time)
    msg = await message.answer("Выберите время доставки:", reply_markup=delivery_time_keyboard())
    data = await state.get_data()
    address_msg = message.message_id
    messages_for_deletion = data.get("messages_for_deletion", [])
    messages_for_deletion.append(msg.message_id)
    messages_for_deletion.append(address_msg)
    await state.update_data(messages_for_deletion=messages_for_deletion)


async def process_delivery_time(callback_query: types.CallbackQuery, state: FSMContext):
    delivery_time_choice = callback_query.data.split('_')[-1]
    data = await state.get_data()
    messages_for_deletion = data.get("messages_for_deletion", [])

    if delivery_time_choice.lower() == "asap":
        await state.update_data(delivery_time="ASAP")
        await state.set_state(Order.accepting_data_processing)
        msg = await callback_query.message.answer(
            "Для завершения оформления заказа необходимо согласие на обработку персональных данных.",
            reply_markup=add_accept_data_processing_button()
        )
        messages_for_deletion.append(msg.message_id)
        await state.update_data(messages_for_deletion=messages_for_deletion)
    elif delivery_time_choice == "scheduled":
        await state.set_state(Order.entering_custom_time)
        msg = await callback_query.message.answer("Введите желаемое время доставки в формате ЧЧ:ММ (например, 14:30):")
        messages_for_deletion.append(msg.message_id)
        await state.update_data(messages_for_deletion=messages_for_deletion)

    await callback_query.answer()


async def process_data_processing(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(data_processing_accepted=True)

    data = await state.get_data()
    delivery_type_id = data.get('delivery_type_id')
    delivery_address = data.get('delivery_address', "")
    delivery_time = data['delivery_time']
    tg_user_id = callback_query.from_user.id

    cart_items = get_cart_items(tg_user_id)

    if not cart_items:
        await callback_query.message.answer("Ваша корзина пуста.")
        await state.clear()
        return

    total_amount = sum(item['product_price'] * item['quantity'] for item in cart_items)

    product_ids_quantities = {item['id_product']: item['quantity'] for item in cart_items}
    order_id = update_order(tg_user_id, delivery_type_id, delivery_address, delivery_time, total_amount,
                            product_ids_quantities)

    if order_id:
        # Состав заказа
        order_details = "\n".join(
            [f"{item['product_name']} (x{item['quantity']}) - {item['product_price'] * item['quantity']} руб." for item
             in cart_items]
        )

        delivery_price = get_delivery_price(delivery_type_id) if total_amount < 1000 else 0
        # Добавляем состав заказа в сообщение
        success_message = (f"Заказ успешно оформлен! Номер вашего заказа: {order_id}\n\nСостав заказа:\n{order_details}"
                           f"\n\nСтоимость доставки: {delivery_price} руб.\n\nИтоговая стоимость: {total_amount + delivery_price} руб.")

        await callback_query.message.answer(success_message)
    else:
        await callback_query.message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.")

    print("messages for deletion:", data.get("messages_for_deletion"))
    await delete_saved_messages(callback_query.bot, callback_query.message.chat.id, state)
    await callback_query.bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=data.get('message_cart')
    )
    await state.clear()


async def process_custom_time(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        # Получаем текущее время
        now = datetime.now()

        # Парсим введённое время
        input_time = datetime.strptime(user_input, "%H:%M")
        delivery_time = input_time.strftime("%H:%M")

        # Сравниваем введённое время с текущим
        input_datetime = datetime.combine(now.date(), input_time.time())
        if input_datetime < now:
            await message.answer("Вы указали время в прошлом. Пожалуйста, введите корректное время доставки.")
            return

        await state.set_state(Order.accepting_data_processing)
        data = await state.get_data()
        messages_for_deletion = data.get("messages_for_deletion", [])

        msg = await message.answer(
            "Для завершения оформления заказа необходимо согласие на обработку персональных данных.",
            reply_markup=add_accept_data_processing_button()
        )
        messages_for_deletion.append(msg.message_id)

        await state.update_data(
            messages_for_deletion=messages_for_deletion,
            delivery_time=delivery_time
        )

    except ValueError:
        await message.answer("Пожалуйста, введите время в правильном формате: ЧЧ:ММ (например, 18:45).")


async def process_edit_item(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart_text = data.get('cart_text')
    product_id = callback_query.data.split('_')[-1]
    text = cart_text + f"\n\nВыберите действие:"
    keyboard = generate_edit_actions_keyboard(product_id)
    await callback_query.message.edit_text(
        text, reply_markup=keyboard
    )


async def process_delete_item(callback_query: types.CallbackQuery, state: FSMContext):
    print(callback_query.data)
    product_id = int(callback_query.data.split('_')[-1])
    tg_user_id = callback_query.from_user.id
    print(tg_user_id)
    try:
        remove_item_from_cart(tg_user_id, product_id)
        await callback_query.answer("Товар успешно удален!")
        await callback_query.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id)
        await view_cart(callback_query.message, state)
    except Exception:
        await callback_query.answer("Произошла ошибка при удалении товара.")


def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(nav_command, Command("nav"))
    dp.message.register(profile_command, Command("profile"))

    dp.message.register(process_name, StateFilter(Registration.waiting_for_name))
    dp.message.register(process_phone, StateFilter(Registration.waiting_for_phone))

    dp.message.register(view_menu, F.text == "Просмотр меню")
    dp.message.register(process_category, lambda msg: msg.text in category_names,
                        ~StateFilter(Admin.adding_product_category), ~StateFilter(Admin.deleting_product_category))

    dp.message.register(view_order_history, F.text == "История заказов")
    dp.message.register(view_order_status, F.text == "Статус заказа")
    dp.message.register(view_cart, F.text == "Корзина")

    dp.callback_query.register(update_quantity_callback, F.data.startswith("update_quantity:"), F.state.any())
    dp.message.register(process_new_quantity, F.state == Order.waiting_for_quantity)

    dp.callback_query.register(process_checkout, F.data == "checkout")
    dp.message.register(nav_command, F.text == "Назад", ~StateFilter(Admin.adding_product_category))

    dp.callback_query.register(process_select_product, F.data.startswith("order_"))
    dp.callback_query.register(process_cancel_select, F.data == "cancel_select",
                               StateFilter(Order.waiting_for_quantity))
    dp.message.register(process_quantity, StateFilter(Order.waiting_for_quantity))

    dp.callback_query.register(process_checkout, F.data.startswith("process_order_"))
    dp.callback_query.register(back_to_cart, F.data == "back_to_cart")
    dp.callback_query.register(process_delivery_type, F.data.startswith("delivery_type_"))
    dp.message.register(process_address, StateFilter(Order.waiting_for_address))
    dp.callback_query.register(process_delivery_time, F.data.startswith("delivery_time_"))
    dp.callback_query.register(process_data_processing, F.data == "accept_data_processing")
    dp.message.register(process_custom_time, StateFilter(Order.entering_custom_time))

    dp.callback_query.register(edit_cart, F.data.startswith("edit_cart_"))
    dp.callback_query.register(process_edit_item, F.data.startswith("edit_item_"))
    dp.callback_query.register(process_delete_item, F.data.startswith("remove_from_cart_"))
    dp.callback_query.register(update_quantity_callback, F.data.startswith("edit_quantity_"))
    dp.message.register(process_new_quantity, StateFilter(Order.waiting_for_new_quantity))