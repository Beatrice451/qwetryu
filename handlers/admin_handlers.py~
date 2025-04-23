import logging
import os
from datetime import datetime

from aiogram import types, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, any_state
from aiogram.types import ContentType, ReplyKeyboardRemove

from db.db_utils import get_admin_by_tg_id, register_admin, delete_product, add_product, verify_admin_password, \
    has_any_admins, get_category_by_name, \
    get_products_by_category_as_menu, get_product_id_by_name, get_todays_orders, update_order_status, get_order_items
from keyboards.keyboards import admin_keyboard, categories_keyboard, get_deletion_keyboard, status_keyboard
from states.states import Admin
from utils.utils import is_admin, delete_saved_messages


async def admin_command(message: types.Message, state: FSMContext):
    admin = get_admin_by_tg_id(message.from_user.id)

    if admin:
        await message.answer("Добро пожаловать в админ-панель!", reply_markup=admin_keyboard())
        logging.info(f"Пользователь {message.from_user.id} вошел в админ-панель")
        return

    if not has_any_admins():

        logging.info(f"Пользователь {message.from_user.id} начал регистрацию администратора")
        await state.set_state(Admin.registering_password)
        await message.answer("Придумайте и введите пароль для регистрации:",
                             reply_markup=ReplyKeyboardRemove())
    else:

        logging.info(f"Пользователь {message.from_user.id} пытается войти в админ-панель")
        await state.set_state(Admin.waiting_for_password)
        await message.answer(
            "У вас нет доступа в админ-панель. Введите пароль администратора (выдаётся самим администратором):")


async def process_admin_registration_password(message: types.Message, state: FSMContext):
    admin = get_admin_by_tg_id(message.from_user.id)
    if admin:
        if verify_admin_password(message.from_user.id, message.text):
            logging.info(f"Пользователь {message.from_user.id} вошел в админ-панель")
            await message.answer("Пароль верный. Админ панель:", reply_markup=admin_keyboard())
            await state.clear()
        else:
            logging.info(f"Пользователь {message.from_user.id} ввел неверный пароль от админ-панели")
            await message.answer("Неверный пароль. Попробуйте еще раз.")

    else:
        await state.update_data(password=message.text)
        await message.answer("Введите ваше имя:")
        await state.set_state(Admin.waiting_for_name)


async def process_admin_password(message: types.Message, state: FSMContext):
    if verify_admin_password(message.from_user.id, message.text):
        logging.info(f"Пользователь {message.from_user.id} вошел в админ-панель")
        await message.answer("Пароль верный. Админ панель:", reply_markup=admin_keyboard())
        register_admin(password=message.text, tg_user_id=message.from_user.id)
        await state.clear()

    else:
        logging.info(f"Пользователь {message.from_user.id} ввел неверный пароль от админ-панели")
        await message.answer("Неверный пароль. Попробуйте еще раз.")


async def process_admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Admin.waiting_for_phone)
    await message.answer("Введите ваш номер телефона:")


async def process_admin_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    name = data['name']
    phone = data['phone']
    password = data.get('password')
    tg_user_id = message.from_user.id

    if register_admin(name=name, phone=phone, tg_user_id=tg_user_id, password=password):
        await message.answer("Регистрация администратора прошла успешно!", reply_markup=admin_keyboard())
        await state.clear()
    else:
        await message.answer("Произошла ошибка при регистрации администратора. Попробуйте позже.")
        await state.clear()


async def set_order_status_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages_for_deletion = data.get("messages_for_deletion", [])
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа.")
        return
    await state.set_state(Admin.waiting_for_order_id)
    msg = await message.answer("Введите ID заказа:", reply_markup=ReplyKeyboardRemove())
    messages_for_deletion.append(msg.message_id)
    await state.update_data(messages_for_deletion=messages_for_deletion)


# TODO create method to get order info by id
async def process_set_order_status_id_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages_for_deletion = data.get("messages_for_deletion", [])
    messages_for_deletion.append(message.message_id)

    try:
        order_id = int(message.text)
    except ValueError:
        await message.answer("Неверный формат ID заказа. Введите число.")
        return
    await state.set_state(Admin.waiting_for_order_status)
    await state.update_data(user_msg=message, messages_for_deletion=messages_for_deletion)
    await message.answer("Укажите новый статус заказа:", reply_markup=status_keyboard(order_id))

async def process_update_order_status(callback_query: types.CallbackQuery, state: FSMContext):
    _, _, order_id, status = callback_query.data.split("_")
    order_id = int(order_id)
    status = str(status)
    data = await state.get_data()
    updated = update_order_status(order_id, status)
    if updated:
        await callback_query.message.edit_text(f"Статус заказа №{order_id} обновлён на: {status}")
        await admin_command(data.get('user_msg'), state)
        await delete_saved_messages(callback_query.bot, callback_query.message.chat.id, state)
    else:
        await callback_query.answer("Не удалось обновить статус.", show_alert=True)

    await state.clear()
    await callback_query.answer()

async def add_product_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа.")
        return

    keyboard = categories_keyboard()
    if keyboard:
        await state.set_state(Admin.adding_product_category)
        await message.answer("Выберите категорию товара:", reply_markup=keyboard)
    else:
        await message.answer("Не удалось загрузить категории меню.")


async def add_product_category_chosen(message: types.Message, state: FSMContext):
    category_id = get_category_by_name(message.text.strip())['id_category']
    await state.update_data(category_id=category_id)
    await state.set_state(Admin.adding_product_name)
    await message.answer("Введите название товара:", reply_markup=ReplyKeyboardRemove())


async def add_product_name_entered(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(Admin.adding_product_description)
    await message.answer("Введите описание товара:")


async def add_product_description_entered(message: types.Message, state: FSMContext):
    await state.update_data(product_description=message.text)
    await state.set_state(Admin.adding_product_price)
    await message.answer("Введите цену товара:")


async def add_product_price_entered(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(product_price=price)
        await state.set_state(Admin.adding_product_image)
        await message.answer("Отправьте изображение товара:")
    except ValueError:
        await message.answer("Неверный формат цены. Введите число.")


async def add_product_image_entered(message: types.Message, state: FSMContext):
    from main import bot
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фотографию товара.")
        return

    # 1. Получаем файл (берём последнее фото - самое качественное)
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    # 2. Скачиваем файл
    local_dir = "resources/images"
    os.makedirs(local_dir, exist_ok=True)

    # 3. Уникальное имя файла
    filename = f"{file_id}.jpg"
    full_path = os.path.join(local_dir, filename)

    # 4. Сохраняем файл локально
    await bot.download_file(file_path, full_path)

    # 5. Обновляем состояние FSM
    await state.update_data(product_image=filename)

    # 6. Получаем все данные
    data = await state.get_data()
    category_id = data.get('category_id')
    product_name = data.get('product_name')
    product_description = data.get('product_description')
    product_price = data.get('product_price')
    product_image = data.get('product_image')

    # logging.info(f"category_id: {category_id} ({type(category_id)})")
    # logging.info(f"product_name: {product_name} ({type(product_name)})")
    # logging.info(f"product_description: {product_description} ({type(product_description)})")
    # logging.info(f"product_price: {product_price} ({type(product_price)})")
    # logging.info(f"product_image: {product_image} ({type(product_image)})")

    # 7. Сохраняем в БД
    if add_product(category_id, product_name, product_description, product_price, product_image):
        await message.answer("Товар успешно добавлен!", reply_markup=admin_keyboard())
    else:
        await message.answer("Произошла ошибка при добавлении товара.")

    await state.clear()


async def delete_product_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа.")
        return
    keyboard = categories_keyboard()
    if keyboard:
        await state.set_state(Admin.deleting_product_category)
        await message.answer("Выберите категорию в которой хотите удалить товар:", reply_markup=keyboard)
    else:
        await message.answer("Не удалось загрузить категории меню.")


async def delete_product_category_chosen(message: types.Message, state: FSMContext):
    category_id = get_category_by_name(message.text.strip())['id_category']
    products = get_products_by_category_as_menu(category_id)
    if products:
        keyboard = get_deletion_keyboard(category_id)
        await state.set_state(Admin.deleting_product_confirmation)
        await message.answer("Выберите товар для удаления:", reply_markup=keyboard)

    else:
        await message.answer("В этой категории нет товаров.")


async def delete_product_confirmation(message: types.Message, state: FSMContext):
    product_id = get_product_id_by_name(message.text.strip())['id_product']
    if delete_product(product_id):
        await message.answer("Товар успешно удален!", reply_markup=admin_keyboard())
        await state.clear()
    else:
        await message.answer("Ошибка при удалении товара.")


async def view_orders(message: types.Message, state: FSMContext):
    orders = get_todays_orders()
    if orders:
        order_details = ""
        for order in orders:
            order_items = get_order_items(order['id_orders'])
            delivery_time = (datetime.min + order['delivery_time']).time()
            deliv_time = (
                delivery_time.strftime('%H:%M') if delivery_time.strftime('%H:%M') != order[
                    'deliv_date'].time().strftime('%H:%M')
                else "Как можно скорее"
            )

            # Форматируем состав заказа
            items_text = ""
            for item in order_items:
                items_text += f"  • {item['name']} × {item['quantity']} = {item['price_to_quan']}₽\n"

            order_details += (
                f"📦 ID Заказа: {order['id_orders']}\n"
                f"🔄 Статус: {order['status']}\n"
                f"📅 Дата оформления: {order['deliv_date'].strftime('%d.%m.%Y %H:%M')}\n"
                f"🚚 Тип доставки: {order['delivery_type']}\n"
                f"💳 Сумма: {order['summa']}₽\n"
                f"📱 Телефон: {order['phone']}\n"
                f"👤 Имя пользователя: {order['name']}\n"
                f"⏱ Время готовности: {deliv_time}\n"
                f"🏠 Адрес доставки: {order['adress'] if order['adress'] else '—'}\n\n"
                f"🛒 Состав заказа:\n{items_text}\n"
                "___________________________\n\n"
            )

        # Разбиваем сообщение, если оно слишком длинное
        if len(order_details) > 4000:
            for chunk in [order_details[i:i + 4000] for i in range(0, len(order_details), 4000)]:
                await message.answer(chunk)
        else:
            await message.answer(f"📊 Заказы за сегодня:\n\n{order_details}")
    else:
        await message.answer("ℹ️ Заказы за сегодняшний день не найдены.")

def register_admin_handlers(dp: Dispatcher):
    # Команды управления админ-панелью
    dp.message.register(admin_command, F.text == "Админ-панель")
    dp.message.register(admin_command, Command("admin"))
    dp.message.register(
        admin_command,
        F.text == "Назад",
        StateFilter(Admin.adding_product_category, Admin.deleting_product_category)
    )

    # Регистрация админа
    dp.message.register(process_admin_password, Admin.waiting_for_password)
    dp.message.register(process_admin_registration_password, Admin.registering_password)
    dp.message.register(process_admin_name, Admin.waiting_for_name)
    dp.message.register(process_admin_phone, Admin.waiting_for_phone)

    # Добавление товаров
    dp.message.register(add_product_start, F.text == "Добавить новый товар")
    dp.message.register(add_product_start, Command("add_product"))
    dp.message.register(
        add_product_category_chosen,
        StateFilter(Admin.adding_product_category)
    )
    dp.message.register(add_product_name_entered, StateFilter(Admin.adding_product_name))
    dp.message.register(add_product_description_entered, StateFilter(Admin.adding_product_description))
    dp.message.register(add_product_price_entered, StateFilter(Admin.adding_product_price))
    dp.message.register(
        add_product_image_entered,
        F.content_type == ContentType.PHOTO,
        StateFilter(Admin.adding_product_image)
    )

    # Удаление товаров
    dp.message.register(delete_product_start, F.text == "Удалить товар", StateFilter(any_state))
    dp.message.register(delete_product_category_chosen, StateFilter(Admin.deleting_product_category))
    dp.message.register(delete_product_confirmation, StateFilter(Admin.deleting_product_confirmation))
    dp.message.register(view_orders, F.text == "Посмотреть заказы")
    dp.message.register(set_order_status_start, F.text == "Изменить статус заказа")
    dp.message.register(process_set_order_status_id_entered, StateFilter(Admin.waiting_for_order_id))
    dp.callback_query.register(process_update_order_status, F.data.startswith("update_status_"))
