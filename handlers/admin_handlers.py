import logging

from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, ReplyKeyboardRemove

from db.db_utils import get_admin_by_tg_id, register_admin, get_products_by_category, \
    delete_product, add_product, verify_admin_password, has_any_admins
from keyboards.keyboards import admin_keyboard, categories_keyboard, product_delete_keyboard
from states.states import Admin
from utils.utils import is_admin


# --- Админ панель ---
async def admin_command(message: types.Message, state: FSMContext):
    admin = get_admin_by_tg_id(message.from_user.id)

    if admin:
        await message.answer("Добро пожаловать в админ-панель!", reply_markup=admin_keyboard())
        logging.info(f"Пользователь {message.from_user.id} вошел в админ-панель")
        return

    if not has_any_admins():
        # Нет админов — запускаем регистрацию
        logging.info(f"Пользователь {message.from_user.id} начал регистрацию администратора")
        await state.set_state(Admin.registering_password)
        await message.answer("Придумайте и введите пароль для регистрации:",
                             reply_markup=ReplyKeyboardRemove())
    else:
        # Есть админы — обычная проверка пароля
        logging.info(f"Пользователь {message.from_user.id} пытается войти в админ-панель")
        await state.set_state(Admin.waiting_for_password)
        await message.answer(
            "У вас нет доступа в админ-панель. Введите пароль администратора (выдаётся самим администратором):")


# Обработчик ввода пароля админа или регистрации админа
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
        # await message.answer("Пароль верный. Админ панель:", reply_markup=admin_keyboard())
        await message.answer("Введите ваше имя:")
        await state.set_state(Admin.waiting_for_name)
        await state.update_data(password=message.text)
    else:
        logging.info(f"Пользователь {message.from_user.id} ввел неверный пароль от админ-панели")
        await message.answer("Неверный пароль. Попробуйте еще раз.")


# Обработчик регистрации администратора
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

    if register_admin(name, phone, tg_user_id, password):
        await message.answer("Регистрация администратора прошла успешно!", reply_markup=admin_keyboard())
        await state.clear()
    else:
        await message.answer("Произошла ошибка при регистрации администратора. Попробуйте позже.")
        await state.clear()


# Добавление товара - выбор категории
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


# Добавление товара - ввод названия
async def add_product_category_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = callback_query.data.split(':')[1]
    await state.update_data(category_id=category_id)
    await state.set_state(Admin.adding_product_name)
    await callback_query.message.edit_text("Введите название товара:")
    await callback_query.answer()


# Добавление товара - ввод описания
async def add_product_name_entered(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(Admin.adding_product_description)
    await message.answer("Введите описание товара:")


# Добавление товара - ввод цены
async def add_product_description_entered(message: types.Message, state: FSMContext):
    await state.update_data(product_description=message.text)
    await state.set_state(Admin.adding_product_price)
    await message.answer("Введите цену товара:")


# Добавление товара - ввод изображения
async def add_product_price_entered(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(product_price=price)
        await state.set_state(Admin.adding_product_image)
        await message.answer("Отправьте изображение товара:")
    except ValueError:
        await message.answer("Неверный формат цены. Введите число.")


# Добавление товара - сохранение
async def add_product_image_entered(message: types.Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1].file_id
        await state.update_data(product_image=photo)
    else:
        await message.answer("Пожалуйста, отправьте фотографию товара.")
        return

    data = await state.get_data()
    category_id = data.get('category_id')
    product_name = data.get('product_name')
    product_description = data.get('product_description')
    product_price = data.get('product_price')
    product_image = data.get('product_image')

    if add_product(category_id, product_name, product_description, product_price, product_image):
        await message.answer("Товар успешно добавлен!")
    else:
        await message.answer("Произошла ошибка при добавлении товара.")

    await state.clear()


# Удаление товара - выбор категории
async def delete_product_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав доступа.")
        return
    keyboard = categories_keyboard()
    if keyboard:
        await state.set_state(Admin.deleting_product_category)
        await message.answer("Выберите категорию товара для удаления:", reply_markup=keyboard)
    else:
        await message.answer("Не удалось загрузить категории меню.")


# Удаление товара - выбор товара для удаления
async def delete_product_category_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = callback_query.data.split(':')[1]
    products = get_products_by_category(category_id)
    if products:
        await state.set_state(Admin.deleting_product_confirmation)
        await callback_query.message.edit_text("Выберите товар для удаления:")
        for product in products:
            markup = product_delete_keyboard(product['id_product'])
            await callback_query.message.answer(f"{product['name']} - {product['price']}", reply_markup=markup)

    else:
        await callback_query.answer("В этой категории нет товаров.")
    await callback_query.answer()


# Удаление товара - подтверждение
async def delete_product_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split(':')[1]
    if delete_product(product_id):
        await callback_query.answer("Товар успешно удален!", show_alert=True)
    else:
        await callback_query.answer("Ошибка при удалении товара.", show_alert=True)
    await callback_query.answer()


def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_command, Command("admin"))
    dp.message.register(process_admin_password, Admin.waiting_for_password)
    dp.message.register(process_admin_registration_password, Admin.registering_password)
    dp.message.register(process_admin_name, Admin.waiting_for_name)
    dp.message.register(process_admin_phone, Admin.waiting_for_phone)

    dp.message.register(add_product_start, F.text == "Добавить новый товар")
    dp.message.register(add_product_start, Command("add_product"))

    dp.callback_query.register(add_product_category_chosen, F.data.startswith("category:"),
                               F.state == Admin.adding_product_category)
    dp.message.register(add_product_name_entered, F.state == Admin.adding_product_name)
    dp.message.register(add_product_description_entered, F.state == Admin.adding_product_description)
    dp.message.register(add_product_price_entered, F.state == Admin.adding_product_price)
    dp.message.register(add_product_image_entered, F.content_type == ContentType.PHOTO,
                        F.state == Admin.adding_product_image)

    dp.message.register(delete_product_start, F.text == "Удалить товар")
    dp.callback_query.register(delete_product_category_chosen, F.data.startswith("category:"),
                               F.state == Admin.deleting_product_category)
    dp.callback_query.register(delete_product_confirmation, F.data.startswith("delete_product:"),
                               F.state == Admin.deleting_product_confirmation)
