from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


class Order(StatesGroup):
    choosing_delivery_type = State()
    waiting_for_address = State()
    choosing_delivery_time = State()
    accepting_data_processing = State()
    waiting_for_quantity = State()
    entering_custom_time = State()
    editing_cart = State()
    waiting_for_new_quantity = State()


# Состояния для админ панели
class Admin(StatesGroup):
    waiting_for_password = State()
    adding_product_category = State()
    adding_product_name = State()
    adding_product_description = State()
    adding_product_price = State()
    adding_product_image = State()
    deleting_product_category = State()
    deleting_product_confirmation = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    registering_password = State()
    waiting_for_order_status = State()
    waiting_for_order_id = State()
