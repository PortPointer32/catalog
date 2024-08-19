import psycopg2
import os

# Данные для подключения к базе данных платежных реквизитов
POSTGRES_DB_PAYMENT = "payment_db"
POSTGRES_USER_PAYMENT = "admin"
POSTGRES_PASSWORD_PAYMENT = "admin"
POSTGRES_HOST_PAYMENT = "localhost"
 
def connect_payment_db():
    return psycopg2.connect(
        dbname=POSTGRES_DB_PAYMENT,
        user=POSTGRES_USER_PAYMENT,
        password=POSTGRES_PASSWORD_PAYMENT,
        host=POSTGRES_HOST_PAYMENT
    )
 
def initialize_payment_db():
    conn = connect_payment_db()
    cursor = conn.cursor()
 
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_details_katalog (
        id SERIAL PRIMARY KEY,
        type TEXT,
        text TEXT,
        coefficient REAL DEFAULT 1.2
    )''')
 
    conn.commit()
    conn.close()

POSTGRES_DB = "pxt"
POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "admin"
POSTGRES_HOST = "localhost"

def connect_db():
    return psycopg2.connect(
        dbname=POSTGRES_DB,   # Имя базы данных
        user=POSTGRES_USER,   # Имя пользователя
        password=POSTGRES_PASSWORD, # Пароль
        host=POSTGRES_HOST    # Хост
    )
    
def initialize():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                username TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT,
                bot_token TEXT,
                bot_username TEXT DEFAULT NULL,
                user_token TEXT DEFAULT NULL,
                FOREIGN KEY (bot_token) REFERENCES tokens(token),
                PRIMARY KEY (user_id, bot_token)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                name TEXT PRIMARY KEY,
                text TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS crypto_prices (
                currency TEXT PRIMARY KEY,
                price REAL
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS payment_details (
                type TEXT PRIMARY KEY,
                text TEXT,
                coefficient REAL DEFAULT 1.2
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS daily_mailings (
                id SERIAL PRIMARY KEY,
                time TEXT,
                text TEXT,
                photo_path TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT,
                city_id INTEGER,
                FOREIGN KEY (city_id) REFERENCES cities(id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_details (
                id SERIAL PRIMARY KEY,
                product_id INTEGER,
                description TEXT,
                weight REAL,
                price REAL,
                districts TEXT,
                klad_type TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS districts_id (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            cursor.execute("INSERT INTO payment_details (type, text) VALUES ('card', 'Пока не установлено.') ON CONFLICT (type) DO NOTHING")
            cursor.execute("INSERT INTO payment_details (type, text) VALUES ('btc', 'Пока не установлено.') ON CONFLICT (type) DO NOTHING")

            cursor.execute("INSERT INTO settings (name, text) VALUES ('help', 'Пока не установлено.') ON CONFLICT (name) DO NOTHING")
            cursor.execute("INSERT INTO settings (name, text) VALUES ('cooperation', 'Пока не установлено.') ON CONFLICT (name) DO NOTHING")
            cursor.execute("INSERT INTO settings (name, text) VALUES ('rules', 'Пока не установлено.') ON CONFLICT (name) DO NOTHING")

            conn.commit()

def add_city_if_not_exists(city_name):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM cities WHERE name = %s", (city_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            cursor.execute("INSERT INTO cities (name) VALUES (%s) RETURNING id", (city_name,))
            conn.commit()
            return cursor.fetchone()[0]

def get_user_bot_info(user_id, bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT bot_username, user_token 
                FROM users 
                WHERE user_id = %s AND bot_token = %s
            """, (user_id, bot_token))
            return cursor.fetchone()

def update_user_bot_info(user_id, bot_token, bot_username=None, user_token=None):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET bot_username = %s, user_token = %s 
                WHERE user_id = %s AND bot_token = %s
            """, (bot_username, user_token, user_id, bot_token))
            conn.commit()

def get_district_name_by_id(district_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM districts_id WHERE id = %s", (district_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def get_district_id_by_name(district_name):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM districts_id WHERE name = %s", (district_name,))
            result = cursor.fetchone()
            return result[0] if result else None

def delete_user_bot_info(user_id, bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET bot_username = NULL, user_token = NULL 
                WHERE user_id = %s AND bot_token = %s
            """, (user_id, bot_token))
            conn.commit()

def get_all_user_tokens():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_token FROM users WHERE user_token IS NOT NULL")
            return cursor.fetchall()

def get_payment_coefficient(payment_type):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT coefficient FROM payment_details_katalog WHERE type = %s", (payment_type,))
    coefficient = cursor.fetchone()
    cursor.close()
    conn.close()
    return coefficient[0] if coefficient else None 

def clear_database():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS product_details, products, cities, daily_mailings, payment_details, crypto_prices, settings, users, tokens CASCADE")
            conn.commit()
            
def get_city_id_by_product(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT city_id
            FROM products
            WHERE id = %s
            """, (product_id,))
            result = cursor.fetchone()
            return result[0] if result else None
            
def update_crypto_price(currency, price):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO crypto_prices (currency, price) VALUES (%s, %s) ON CONFLICT (currency) DO UPDATE SET price = EXCLUDED.price", (currency, price))
            conn.commit()

def get_crypto_price(currency):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT price FROM crypto_prices WHERE currency = %s", (currency,))
            result = cursor.fetchone()
            return result[0] if result else None
            
def add_daily_mailing(time, text, photo_path):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO daily_mailings (time, text, photo_path) VALUES (%s, %s, %s)", (time, text, photo_path))
            conn.commit()

def delete_daily_mailing(id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM daily_mailings WHERE id = %s", (id,))
            conn.commit()

def get_daily_mailings():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM daily_mailings")
            return cursor.fetchall()

def get_daily_mailing_by_id(id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM daily_mailings WHERE id = %s", (id,))
            return cursor.fetchone()

def add_token(token, username):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO tokens (token, username) VALUES (%s, %s)", (token, username))
            conn.commit()

def delete_token(value):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE bot_token = %s", (value,))
    cursor.execute("DELETE FROM tokens WHERE token = %s", (value,))
    conn.commit()
    cursor.close()
    conn.close()

def delete_data(value):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE bot_token = %s", (value,))
    cursor.execute("DELETE FROM tokens WHERE token = %s", (value,))
    conn.commit()
    cursor.close()
    conn.close()

def get_tokens():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT token, username FROM tokens")
            return cursor.fetchall()

def add_product(product_name, city_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO products (name, city_id) VALUES (%s, %s) RETURNING id", (product_name, city_id))
            conn.commit()
            return cursor.fetchone()[0]

def get_total_users_count():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]

def get_users_count_of_bot(bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE bot_token = %s", (bot_token,))
            return cursor.fetchone()[0]

def get_cities():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM cities")
            return cursor.fetchall()

def get_city_name(city_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM cities WHERE id = %s", (city_id,))
            return cursor.fetchone()

def get_products_by_city(city_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products WHERE city_id = %s", (city_id,))
            return cursor.fetchall()

def get_product_name(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
            return cursor.fetchone()

def get_product_price(product_id, weight):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT price FROM product_details WHERE product_id = %s AND weight = %s", (product_id, weight))
            result = cursor.fetchone()
            return result[0] if result else None

def get_product_details_by_weight(product_id, weight):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            query = """
            SELECT pd.description, pd.weight, pd.price, pd.districts, pd.klad_type, p.city_id 
            FROM product_details pd
            JOIN products p ON pd.product_id = p.id
            WHERE pd.product_id = %s AND CAST(pd.weight AS NUMERIC(10,2)) = CAST(%s AS NUMERIC(10,2))
            """
            cursor.execute(query, (product_id, weight))
            rows = cursor.fetchall()
            details_list = []
            for row in rows:
                details = {
                    "description": row[0],
                    "weight": row[1],
                    "price": row[2],
                    "districts": row[3],
                    "klad_type": row[4],
                    "city_id": row[5]
                }
                details_list.append(details)
            return details_list

def delete_city(city_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM product_details WHERE product_id IN (SELECT id FROM products WHERE city_id = %s)", (city_id,))
            
            cursor.execute("DELETE FROM products WHERE city_id = %s", (city_id,))

            cursor.execute("DELETE FROM cities WHERE id = %s", (city_id,))
            conn.commit()
            
def delete_product(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM product_details WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()
            
def get_full_database_info():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM cities")
            cities_info = cursor.fetchall()
            cities_output = ["Города:"] + [f"ID: {city[0]}, Название: {city[1]}" for city in cities_info]

            cursor.execute("SELECT * FROM products")
            products_info = cursor.fetchall()
            products_output = ["Товары:"] + [f"ID: {prod[0]}, Название: {prod[1]}, Категория ID: {prod[2]}" for prod in products_info]

            return "\n".join(cities_output + products_output)

def add_product_details(product_id, description, weight, price, districts, klad_type):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            for district in districts.split(','):
                district_id = get_district_id_by_name(district.strip())
                if not district_id:
                    cursor.execute("INSERT INTO districts_id (name) VALUES (%s)", (district.strip(),))
                    conn.commit()
            
            cursor.execute("INSERT INTO product_details (product_id, description, weight, price, districts, klad_type) VALUES (%s, %s, %s, %s, %s, %s)",
                           (product_id, description, weight, price, districts, klad_type))
            conn.commit()

def get_product_details(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT description, weight, price, districts, klad_type FROM product_details WHERE product_id = %s", (product_id,))
            rows = cursor.fetchall()
            details_list = []
            for row in rows:
                details = {
                    "description": row[0],
                    "weight": row[1],
                    "price": row[2],
                    "districts": row[3],
                    "klad_type": row[4]
                }
                details_list.append(details)
            return details_list

def get_bot_data(token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, token FROM tokens WHERE token = %s", (token,))
            return cursor.fetchone()

def add_user(user_id, bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (user_id, bot_token) VALUES (%s, %s)", (user_id, bot_token))
            conn.commit()

def get_users_by_token(bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE bot_token = %s", (bot_token,))
            return cursor.fetchall()

def check_user_exists(user_id, bot_token):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s AND bot_token = %s", (user_id, bot_token))
            return cursor.fetchone() is not None

def get_help_text():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT text FROM settings WHERE name = 'help'")
            return cursor.fetchone()[0]

def set_help_text(new_text):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE settings SET text = %s WHERE name = 'help'", (new_text,))
            conn.commit()

def get_cooperation_text():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT text FROM settings WHERE name = 'cooperation'")
            return cursor.fetchone()[0]

def set_cooperation_text(new_text):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE settings SET text = %s WHERE name = 'cooperation'", (new_text,))
            conn.commit()

def get_rules_text():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT text FROM settings WHERE name = 'rules'")
            return cursor.fetchone()[0]

def set_rules_text(new_text):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE settings SET text = %s WHERE name = 'rules'", (new_text,))
            conn.commit()

def get_payment_details(payment_type):
    conn = connect_payment_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT text FROM payment_details_katalog WHERE type = %s", (payment_type,))
        row = cursor.fetchone()
        return row[0] if row else "Реквизиты не найдены."
    finally:
        cursor.close()
        conn.close()

def set_payment_details(payment_type, new_text):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payment_details_katalog SET text = %s WHERE type = %s", (new_text, payment_type))
    conn.commit()
    cursor.close()
    conn.close()
            
def get_product_weights(product_id):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT weight FROM product_details WHERE product_id = %s", (product_id,))
            weights = cursor.fetchall()
            return [weight[0] for weight in weights]
        
def get_active_payment_types():
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM payment_details_katalog WHERE boolean = 1")
    active_types = cursor.fetchall()
    cursor.close()
    conn.close()
    return [type[0] for type in active_types]

def toggle_payment_boolean(payment_type):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT boolean FROM payment_details_katalog WHERE type = %s", (payment_type,))
    current_value = cursor.fetchone()
    if current_value is not None:
        new_value = 0 if current_value[0] == 1 else 1
        cursor.execute("UPDATE payment_details_katalog SET boolean = %s WHERE type = %s", (new_value, payment_type))
        conn.commit()
        cursor.close()
        conn.close()
        return new_value 
    cursor.close()
    conn.close()
    return None

def get_payment_boolean(payment_type):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT boolean FROM payment_details_katalog WHERE type = %s", (payment_type,))
    boolean = cursor.fetchone()
    cursor.close()
    conn.close()
    return boolean[0] if boolean else None 

def set_payment_coefficient(payment_type, new_coefficient):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payment_details_katalog SET coefficient = %s WHERE type = %s", (new_coefficient, payment_type))
    conn.commit()
    cursor.close()
    conn.close()

def get_payment_methods():
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type, text FROM payment_details_katalog")
    methods = cursor.fetchall()
    cursor.close()
    conn.close()
    return methods

def get_enabled_payment_methods():
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type, text FROM payment_details_katalog WHERE boolean = 1")
    methods = cursor.fetchall()
    cursor.close()
    conn.close()
    return methods

def set_payment_method_status(payment_type, new_status):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payment_details_katalog SET boolean = %s WHERE type = %s", (new_status, payment_type))
    conn.commit()
    cursor.close()
    conn.close()

def set_payment_photo(payment_type, photo_path):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payment_details_katalog SET photo_path = %s WHERE type = %s", (photo_path, payment_type))
    conn.commit()
    cursor.close()
    conn.close()

def get_payment_method_status(payment_type):
    conn = connect_payment_db()
    cursor = conn.cursor()
    cursor.execute("SELECT boolean FROM payment_details_katalog WHERE type = %s", (payment_type,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else False