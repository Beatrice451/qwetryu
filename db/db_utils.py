import logging
from datetime import datetime

import bcrypt
import mysql.connector

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

logging.basicConfig(level=logging.INFO)


def connect_to_db():
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return mydb
    except mysql.connector.Error as err:
        logging.error(f"Ошибка подключения к базе данных: {err}")
        return None


def register_user(name, phone, tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = "INSERT INTO user (name, phone, tg_user_id) VALUES (%s, %s, %s)"
        val = (name, phone, tg_user_id)
        try:
            mycursor.execute(sql, val)
            mydb.commit()
            logging.info(f"Пользователь {name} (ID: {tg_user_id}) успешно зарегистрирован.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка регистрации пользователя: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def get_user(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM user WHERE tg_user_id = %s"
        val = (tg_user_id,)
        try:
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            return result
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения пользователя: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_menu_categories():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = "SELECT id_category, name_cat FROM category"
        try:
            mycursor.execute(sql)
            categories = mycursor.fetchall()
            return categories
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения категорий: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_products_by_category(category_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_product, name, descript, price, photo FROM product WHERE id_category = %s AND is_deleted = 0"
        val = (category_id,)
        try:
            mycursor.execute(sql, val)
            products = mycursor.fetchall()
            return products
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения продуктов: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None

def cancel_order_by_id(order_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = """
        UPDATE Orders
        SET status = 'Отменен'
        WHERE id_orders = %s;
        """
        val = (order_id,)
        try:
            mycursor.execute(sql, val)
            mydb.commit()
            print(f"Заказ {order_id} успешно отменен")
        except mysql.connector.Error as err:
            logging.error(f"Ошибка при отмене заказа: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None

def get_order_history(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = """
            SELECT
                o.id_orders,
                o.deliv_date,
                o.summa,
                dt.name,
                o.delivery_time,
                o.status,
                u.phone
            FROM
                orders o
            JOIN
                user u ON o.id_user = u.id_user
            JOIN
                delivtype dt ON o.id_type = dt.id_type
            WHERE
                u.tg_user_id = %s
                AND o.deliv_date >= CURDATE() - INTERVAL 2 DAY
            ORDER BY
                o.deliv_date DESC
            LIMIT 10;
        """
        val = (tg_user_id,)
        try:
            mycursor.execute(sql, val)
            orders = mycursor.fetchall()
            return orders
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения истории заказов: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_category_by_name(category_name):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM category WHERE name_cat = %s"
        val = (category_name,)
        try:
            mycursor.execute(sql, val)
            category = mycursor.fetchone()
            return category
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения категории: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_order_items(order_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = """
            SELECT
                p.id_product,
                p.name,
                b.quantity,
                b.price_to_quan
            FROM
                basket b
            JOIN
                product p ON b.id_product = p.id_product
            WHERE
                b.id_orders = %s;
        """
        val = (order_id,)
        try:
            mycursor.execute(sql, val)
            items = mycursor.fetchall()
            return items
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения товаров заказа: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_order_status(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = """
            SELECT status, deliv_date
            FROM orders
            WHERE id_user = (SELECT id_user FROM user WHERE tg_user_id = %s)
            AND status != 'Корзина'
            ORDER BY deliv_date DESC
            LIMIT 1;
        """
        val = (tg_user_id,)
        try:
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            if result:
                return result
            else:
                return None
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения статуса заказа: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_delivery_price(delivery_type_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = "SELECT price_dost FROM delivtype WHERE id_type = %s"
        val = (delivery_type_id,)
        try:
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения стоимости доставки: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


# TODO implement delivery_time
def update_order(tg_user_id, delivery_type_id, delivery_address, delivery_time, order_total, cart_items):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql_get_user_id = "SELECT id_user FROM user WHERE tg_user_id = %s"
        try:
            mycursor.execute(sql_get_user_id, (tg_user_id,))
            user_id_result = mycursor.fetchone()
            if not user_id_result:
                logging.error(f"Пользователь с tg_user_id {tg_user_id} не найден.")
                return None
            id_user = user_id_result[0]

            # Получаем ID заказа в статусе "корзина"
            sql_get_order = "SELECT id_orders FROM orders WHERE id_user = %s AND status = 'корзина'"
            mycursor.execute(sql_get_order, (id_user,))
            order_result = mycursor.fetchone()
            if not order_result:
                logging.error(f"Заказ в статусе 'корзина' не найден для пользователя {tg_user_id}.")
                return None
            order_id = order_result[0]
            # delivery_price_result = (get_delivery_price(delivery_type_id),)
            # if delivery_type_id == 2 and order_total > 1000:
            #     delivery_price_result = (0,)
            # else:
            #     order_total += delivery_price_result[0]
            if delivery_time == "ASAP":
                delivery_time = datetime.now()

            # Обновляем заказ
            sql_update_order = """
                UPDATE orders
                SET deliv_date = NOW(),
                    summa = %s,
                    id_type = %s,
                    adress = %s,
                    delivery_time = %s,
                    status = 'Оформлен'
                WHERE id_orders = %s
            """
            mycursor.execute(sql_update_order,
                             (order_total, delivery_type_id, delivery_address,
                              delivery_time,
                              order_id)
                             )
            mydb.commit()
            # Очищаем старые товары
            mycursor.execute("DELETE FROM basket WHERE id_orders = %s", (order_id,))

            # Добавляем новые товары
            for product_id, quantity in cart_items.items():
                product_details = get_product_details(product_id)
                if product_details:
                    price_to_quan = product_details['price'] * quantity
                    sql_item = "INSERT INTO basket (id_orders, id_product, quantity, price_to_quan) VALUES (%s, %s, %s, %s)"
                    val_item = (order_id, product_id, quantity, price_to_quan)
                    mycursor.execute(sql_item, val_item)

            mydb.commit()
            logging.info(f"Заказ (ID: {order_id}) успешно обновлён для пользователя {tg_user_id}.")
            sql_new_cart = """
                INSERT INTO orders (id_user, deliv_date, summa, id_type, adress, delivery_time, status)
                VALUES (%s, NOW(), 0, NULL, '', NULL, 'Корзина')
            """
            mycursor.execute(sql_new_cart, (id_user,))
            mydb.commit()
            return order_id
        except mysql.connector.Error as err:
            logging.error(f"Ошибка обновления заказа: {err}")
            mydb.rollback()
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def delete_product(product_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = "UPDATE product SET is_deleted = 1 WHERE id_product = %s;"
        try:
            mycursor.execute(sql, (product_id,))
            mydb.commit()
            logging.info(f"Товар (ID: {product_id}) успешно удален.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка при удалении товара: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def add_product(category_id, product_name, product_description, product_price, product_image):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = """
            INSERT INTO product (id_category, name, descript, price, photo)
            VALUES (%s, %s, %s, %s, %s)
        """
        val = (category_id, product_name, product_description, product_price, product_image)
        try:
            mycursor.execute(sql, val)
            mydb.commit()
            logging.info(f"Товар {product_name} успешно добавлен.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка при добавлении товара: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def get_todays_orders():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = """
            SELECT
                o.id_orders,
                o.deliv_date,
                o.summa,
                o.delivery_time,
                dt.name AS delivery_type,
                o.delivery_time,
                o.status,
                o.adress,
                u.phone,
                u.tg_user_id,
                u.name
            FROM
                orders o
            JOIN
                user u ON o.id_user = u.id_user
            JOIN
                delivtype dt ON o.id_type = dt.id_type
            WHERE DATE(o.deliv_date) = CURDATE() AND o.status != 'Корзина' AND o.status != 'Завершен'
            ORDER BY o.deliv_date DESC;
        """
        try:
            mycursor.execute(sql)
            orders = mycursor.fetchall()
            return orders
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения заказов за сегодня: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def update_order_status(order_id, status):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = "UPDATE orders SET status = %s WHERE id_orders = %s"
        try:
            mycursor.execute(sql, (status, order_id))
            mydb.commit()
            logging.info(f"Статус заказа {order_id} обновлен на {status}.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка обновления статуса заказа: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return True


def get_admin_by_tg_id(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM admin WHERE tg_user_id = %s"
        try:
            mycursor.execute(sql, (tg_user_id,))
            admin = mycursor.fetchone()
            return admin
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения данных админа: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def register_admin(tg_user_id: int, password: str, name: str = None, phone: str = None):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sql = "INSERT INTO admin (name, phone, tg_user_id, password) VALUES (%s, %s, %s, %s)"
        val = (name, phone, tg_user_id, hashed_password)
        try:
            mycursor.execute(sql, val)
            mydb.commit()
            logging.info(f"Администратор {name} (ID: {tg_user_id}) успешно зарегистрирован.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка регистрации администратора: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def verify_admin_password(tg_user_id, password):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT password FROM admin LIMIT 1"
        try:
            mycursor.execute(sql)
            admin = mycursor.fetchone()
            if admin:
                hashed_password = admin['password']
                return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            else:
                return False
        except mysql.connector.Error as err:
            logging.error(f"Ошибка верификации пароля: {err}")
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def get_delivery_types():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_type, name, price_dost FROM delivtype"
        try:
            mycursor.execute(sql)
            delivery_types = mycursor.fetchall()
            return delivery_types
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения типов доставки: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_delivery_type_by_id(delivery_type_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_type, delivery_type, price_dost FROM delivtype WHERE id_type = %s"
        try:
            mycursor.execute(sql, (delivery_type_id,))
            delivery_type = mycursor.fetchone()
            return delivery_type
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения типа доставки: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def add_to_cart(tg_user_id, product_id, quantity):
    mydb = connect_to_db()
    if not mydb:
        return False

    try:
        mycursor = mydb.cursor(dictionary=True)

        # 1. Получаем id пользователя
        sql_get_user = "SELECT id_user FROM user WHERE tg_user_id = %s"
        mycursor.execute(sql_get_user, (tg_user_id,))
        user = mycursor.fetchone()
        if not user:
            logging.error(f"Пользователь с tg_user_id {tg_user_id} не найден.")
            return False
        id_user = user['id_user']

        # 2. Проверяем наличие открытой корзины (status='cart')
        sql_find_cart = "SELECT id_orders FROM orders WHERE id_user = %s AND status = 'Корзина'"
        mycursor.execute(sql_find_cart, (id_user,))
        order = mycursor.fetchone()

        if order:
            order_id = order['id_orders']
        else:
            # 3. Если корзины нет — создаем новую
            sql_create_cart = "INSERT INTO orders (id_user, status) VALUES (%s, 'Корзина')"
            mycursor.execute(sql_create_cart, (id_user,))
            order_id = mycursor.lastrowid

        # 4. Проверяем, есть ли уже этот товар в корзине
        sql_check_product = """
            SELECT id_basket, quantity FROM basket
            WHERE id_orders = %s AND id_product = %s
        """
        mycursor.execute(sql_check_product, (order_id, product_id))
        basket_item = mycursor.fetchone()

        if basket_item:
            # 5. Товар уже есть — обновляем количество
            new_quantity = basket_item['quantity'] + quantity
            sql_update_quantity = "UPDATE basket SET quantity = %s WHERE id_basket = %s"
            mycursor.execute(sql_update_quantity, (new_quantity, basket_item['id_basket']))
        else:
            # 6. Получаем цену товара
            sql_get_price = "SELECT price FROM product WHERE id_product = %s"
            mycursor.execute(sql_get_price, (product_id,))
            product = mycursor.fetchone()
            if not product:
                logging.error(f"Товар с id {product_id} не найден.")
                return False
            price_to_quan = product['price'] * quantity

            # 7. Вставляем новую позицию в корзину
            sql_add_item = """
                INSERT INTO basket (id_orders, id_product, quantity, price_to_quan)
                VALUES (%s, %s, %s, %s)
            """
            mycursor.execute(sql_add_item, (order_id, product_id, quantity, price_to_quan))

        mydb.commit()
        logging.info(f"Товар {product_id} добавлен в корзину пользователя {tg_user_id}")
        return True

    except mysql.connector.Error as err:
        logging.error(f"Ошибка при добавлении в корзину: {err}")
        mydb.rollback()
        return False
    finally:
        mycursor.close()
        mydb.close()


def get_cart_items(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql_get_user_id = "SELECT id_user FROM user WHERE tg_user_id = %s"
        try:
            mycursor.execute(sql_get_user_id, (tg_user_id,))
            user_id_result = mycursor.fetchone()
            if not user_id_result:
                logging.error(f"Пользователь с tg_user_id {tg_user_id} не найден.")
                return None
            id_user = user_id_result['id_user']

            # Получаем id заказов пользователя
            sql_get_orders = """
            SELECT id_orders
            FROM orders
            WHERE id_user = %s
            AND status = 'Корзина'
            """
            mycursor.execute(sql_get_orders, (id_user,))
            orders_result = mycursor.fetchall()
            if not orders_result:
                logging.error(f"У пользователя {tg_user_id} нет активных заказов.")
                return None

            # Создаём список id заказов
            order_ids = [order['id_orders'] for order in orders_result]

            # Получаем товары из корзины, относящиеся к этим заказам
            sql = """
            SELECT
                b.id_basket,
                b.id_product,
                b.quantity,
                b.price_to_quan,
                p.name as product_name,
                p.price as product_price
            FROM
                basket b
            JOIN
                product p ON b.id_product = p.id_product
            WHERE
                b.id_orders IN (%s)  -- Товары, привязанные к активным заказам
            """
            format_strings = ','.join(['%s'] * len(order_ids))  # Подготовка строки для IN
            sql = sql % format_strings
            mycursor.execute(sql, tuple(order_ids))
            cart_items = mycursor.fetchall()
            return cart_items
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения товаров из корзины: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_orders_today():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)  # Используем dictionary, чтобы получать результаты как словарь
        try:
            # Получаем сегодняшнюю дату в формате 'YYYY-MM-DD'
            today = datetime.today()

            # Запрос для получения всех заказов, сделанных сегодня
            sql = """
                SELECT o.id_orders, o.status, o.created_at, o.delivery_type, o.total_amount, u.phone, u.name AS user_name
                FROM orders o
                JOIN user u ON o.id_user = u.id_user
                WHERE o.created_at >= %s AND o.created_at < %s
            """
            # Устанавливаем диапазон дат: с начала сегодняшнего дня до конца дня
            start_of_day = f"{today} 00:00:00"
            end_of_day = f"{today} 23:59:59"

            mycursor.execute(sql, (start_of_day, end_of_day))
            orders = mycursor.fetchall()

            return orders
        except mysql.connector.Error as err:
            print(f"Ошибка при запросе заказов: {err}")
            return []
        finally:
            mycursor.close()
            mydb.close()
    return []

def update_cart_item_quantity(tg_user_id, product_id, quantity):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        try:
            # Шаг 1: Найдем заказ пользователя со статусом "Корзина"
            sql_find_cart = """
                SELECT id_orders 
                FROM orders 
                WHERE id_user = (SELECT id_user FROM user WHERE tg_user_id = %s) 
                AND status = 'Корзина'
                LIMIT 1
            """
            mycursor.execute(sql_find_cart, (tg_user_id,))
            cart_id = mycursor.fetchone()

            if cart_id is None:
                logging.warning(f"Корзина для пользователя с tg_user_id={tg_user_id} не найдена.")
                return False

            cart_id = cart_id[0]  # Получаем id_orders корзины

            # Шаг 2: Находим товар в корзине по id_product
            sql_find_cart_item = """
                SELECT id_basket, quantity 
                FROM basket 
                WHERE id_orders = %s AND id_product = %s
            """
            mycursor.execute(sql_find_cart_item, (cart_id, product_id))
            cart_item = mycursor.fetchone()

            if cart_item is None:
                logging.warning(f"Товар с id_product={product_id} не найден в корзине для пользователя с tg_user_id={tg_user_id}.")
                return False

            id_basket, old_quantity = cart_item  # Получаем id_basket и старое количество товара

            # Шаг 3: Получим цену товара
            sql_find_product_price = """
                SELECT price FROM product WHERE id_product = %s
            """
            mycursor.execute(sql_find_product_price, (product_id,))
            product_price = mycursor.fetchone()

            if product_price is None:
                logging.warning(f"Товар с id_product={product_id} не найден.")
                return False

            product_price = product_price[0]  # Получаем цену товара

            # Шаг 4: Обновляем количество товара и пересчитываем цену
            sql_update = """
                UPDATE basket 
                SET quantity = %s, 
                    price_to_quan = %s * %s
                WHERE id_basket = %s
            """
            val = (quantity, product_price, quantity, id_basket)
            mycursor.execute(sql_update, val)
            mydb.commit()

            if mycursor.rowcount > 0:
                logging.info(f"Количество товара с id_basket={id_basket} в корзине обновлено на {quantity}.")
                return True
            else:
                logging.warning(f"Не удалось обновить товар с id_basket={id_basket} в корзине для пользователя с tg_user_id={tg_user_id}.")
                return False

        except mysql.connector.Error as err:
            logging.error(f"Ошибка обновления количества товара в корзине: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False



def remove_item_from_cart(tg_user_id, product_id):
    mydb = connect_to_db()
    try:
        mycursor = mydb.cursor()
        mydb.start_transaction()

        # Удаление товара из корзины
        sql_basket = """
            DELETE FROM basket
            WHERE id_orders IN (
                SELECT id_orders FROM orders
                WHERE id_user = (SELECT id_user FROM user WHERE tg_user_id = %s)
                AND status = 'Корзина'
            )
            AND id_product = %s
        """
        print("executing sql_basket")
        mycursor.execute(sql_basket, (tg_user_id, product_id))
        mydb.commit()

        # Удаление заказа, если корзина пуста
        sql_orders = """
            DELETE FROM orders
            WHERE id_user = (SELECT id_user FROM user WHERE tg_user_id = %s)
            AND status = 'Корзина'
            AND NOT EXISTS (
                SELECT 1 FROM basket WHERE id_orders = orders.id_orders
            )
        """
        print("executing sql_orders")
        mycursor.execute(sql_orders, (tg_user_id,))

        mydb.commit()
        return mycursor.rowcount > 0
    except Exception as e:
        mydb.rollback()
        logging.error(f"Ошибка при удалении товара: {e}")
        return False
    finally:
        mycursor.close()
        mydb.close()


def has_any_admins():
    """
    Проверяет, есть ли хотя бы один администратор в базе данных.

    :return: True, если есть хотя бы один администратор, иначе False.
    """
    mydb = connect_to_db()
    if mydb is None:
        return False

    try:
        with mydb.cursor() as mycursor:
            mycursor.execute("SELECT COUNT(*) FROM admin")
            result = mycursor.fetchone()
            logging.info(f"Количество администраторов: {result[0]}")
            return bool(result and result[0] > 0)
    except mysql.connector.Error as err:
        logging.error(f"Ошибка проверки наличия администраторов: {err}")
        return False
    finally:
        mydb.close()
        mycursor.close()


def get_product_details(product_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM product WHERE id_product = %s"
            mycursor.execute(sql, (product_id,))
            product = mycursor.fetchone()
            return product
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения деталей продукта: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()


def get_products_by_category_as_menu(category_id) -> dict | None:
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_product, name FROM product WHERE id_category = %s AND is_deleted = 0"
        val = (category_id,)
        try:
            mycursor.execute(sql, val)
            products = mycursor.fetchall()
            return products
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения продуктов: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_product_id_by_name(product_name):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_product FROM product WHERE name = %s"
        val = (product_name,)
        try:
            mycursor.execute(sql, val)
            product_id = mycursor.fetchone()
            return product_id
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения ID продукта: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None

def get_admins():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        sql = """
        SELECT id_admin
        FROM admin
        LIMIT 1;
        """
        try:
            mycursor.execute(sql)
            admins = mycursor.fetchall()
            return admins
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения администраторов: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()