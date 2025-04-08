import mysql.connector
import logging
import bcrypt  # Для хеширования паролей
from datetime import datetime

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
        sql = "SELECT id_product, name, price FROM product WHERE id_category = %s"
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


def get_order_history(tg_user_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = """
            SELECT
                o.id_orders,
                o.date,
                o.summa,
                dt.delivery_type,
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
            ORDER BY
                o.date DESC;
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
            SELECT status
            FROM orders
            WHERE id_user = (SELECT id_user FROM user WHERE tg_user_id = %s)
            ORDER BY date DESC
            LIMIT 1;
        """
        val = (tg_user_id,)
        try:
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения статуса заказа: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def create_order(tg_user_id, delivery_type_id, delivery_address, delivery_time, order_total, cart_items):
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
            sql = """
                INSERT INTO orders (id_user, date, summa, id_type, delivery_address, delivery_time, status)
                VALUES (%s, NOW(), %s, %s, %s, %s, 'Оформлен');
            """
            val = (id_user, order_total, delivery_type_id, delivery_address, delivery_time)
            mycursor.execute(sql, val)
            order_id = mycursor.lastrowid
            mydb.commit()
            for product_id, quantity in cart_items.items():
                product_details = get_product_details(product_id)
                if product_details:
                    price_to_quan = product_details['price'] * quantity
                    sql_item = "INSERT INTO basket (id_orders, id_product, quantity, price_to_quan) VALUES (%s, %s, %s, %s)"
                    val_item = (order_id, product_id, quantity, price_to_quan)
                    mycursor.execute(sql_item, val_item)
            mydb.commit()
            logging.info(f"Новый заказ (ID: {order_id}) успешно создан для пользователя {tg_user_id}.")
            return order_id
        except mysql.connector.Error as err:
            logging.error(f"Ошибка создания заказа: {err}")
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
        sql = "DELETE FROM product WHERE id_product = %s"
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
                o.date,
                o.summa,
                dt.delivery_type,
                o.delivery_time,
                o.status,
                u.phone,
                u.tg_user_id
            FROM
                orders o
            JOIN
                user u ON o.id_user = u.id_user
            JOIN
                delivtype dt ON o.id_type = dt.id_type
            WHERE DATE(o.date) = CURDATE()
            ORDER BY o.date DESC;
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


def register_admin(name, phone, tg_user_id, password):
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
        sql = "SELECT password FROM admin WHERE tg_user_id = %s"
        try:
            mycursor.execute(sql, (tg_user_id,))
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


def get_product_details(product_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT name, price FROM product WHERE id_product = %s"
        try:
            mycursor.execute(sql, (product_id,))
            product = mycursor.fetchone()
            return product
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения деталей товара: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def get_delivery_types():
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT id_type, delivery_type, price_dost FROM delivtype"
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
    if mydb:
        mycursor = mydb.cursor()
        sql_get_user_id = "SELECT id_user FROM user WHERE tg_user_id = %s"
        try:
            mycursor.execute(sql_get_user_id, (tg_user_id,))
            user_id_result = mycursor.fetchone()
            if not user_id_result:
                logging.error(f"Пользователь с tg_user_id {tg_user_id} не найден.")
                return False
            id_user = user_id_result[0]
            sql_check_cart = "SELECT id_basket, quantity FROM basket WHERE id_user = %s AND id_product = %s AND id_orders IS NULL"
            mycursor.execute(sql_check_cart, (id_user, product_id))
            cart_item = mycursor.fetchone()
            if cart_item:
                new_quantity = cart_item[1] + quantity
                sql_update_cart = "UPDATE basket SET quantity = %s WHERE id_basket = %s"
                mycursor.execute(sql_update_cart, (new_quantity, cart_item[0]))
            else:
                product_details = get_product_details(product_id)
                if not product_details:
                    logging.error(f"Товар с id_product {product_id} не найден.")
                    return False
                price_to_quan = product_details['price'] * quantity
                sql_add_to_cart = "INSERT INTO basket (id_user, id_product, quantity, price_to_quan) VALUES (%s, %s, %s, %s)"
                mycursor.execute(sql_add_to_cart, (id_user, product_id, quantity, price_to_quan))

            mydb.commit()
            logging.info(f"Товар (ID: {product_id}) добавлен в корзину для пользователя {tg_user_id}.")
            return True

        except mysql.connector.Error as err:
            logging.error(f"Ошибка добавления в корзину: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


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
            id_user = user_id_result[0]

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
                b.id_user = %s AND b.id_orders IS NULL
            """
            mycursor.execute(sql, (id_user,))
            cart_items = mycursor.fetchall()
            return cart_items
        except mysql.connector.Error as err:
            logging.error(f"Ошибка получения товаров из корзины: {err}")
            return None
        finally:
            mycursor.close()
            mydb.close()
    return None


def update_cart_item_quantity(cart_item_id, quantity):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        try:
            sql = "UPDATE basket SET quantity = %s, price_to_quan = (SELECT price FROM product WHERE id_product = id_product) * %s WHERE id_basket = %s"
            val = (quantity, quantity, cart_item_id)
            mycursor.execute(sql, val)
            mydb.commit()
            logging.info(f"Количество товара в корзине (ID: {cart_item_id}) обновлено на {quantity}.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка обновления количества товара в корзине: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False


def remove_cart_item(cart_item_id):
    mydb = connect_to_db()
    if mydb:
        mycursor = mydb.cursor()
        try:
            sql = "DELETE FROM basket WHERE id_basket = %s"
            mycursor.execute(sql, (cart_item_id,))
            mydb.commit()
            logging.info(f"Товар (ID: {cart_item_id}) удален из корзины.")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Ошибка удаления товара из корзины: {err}")
            mydb.rollback()
            return False
        finally:
            mycursor.close()
            mydb.close()
    return False
