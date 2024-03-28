import sqlite3
import logging

DB_DIR = 'db'
DB_NAME = 'gpt_helper.db'
DB_TABLE_USERS_NAME = 'users'

# Функция для подключения к базе данных или создания новой, если её ещё нет
def create_db(database_name=DB_NAME):
    db_path = f'{database_name}'
    connection = sqlite3.connect(db_path)
    connection.close()

# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()

# Функция для выполнения любого sql-запроса для получения данных (возвращает значение)
def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows

# Функция для создания новой таблицы (если такой ещё нет)
# Получает название и список колонок в формате ИМЯ: ТИП
# Создаёт запрос CREATE TABLE IF NOT EXISTS имя_таблицы (колонка1 ТИП, колонка2 ТИП)
def create_table(table_name):
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name} ' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'subject TEXT, ' \
                f'level TEXT, ' \
                f'task TEXT, ' \
                f'answer TEXT, ' \
                f'timestamp TEXT)'
    execute_query(sql_query)

# Функция для вывода всей таблицы (для проверки)
# Создаёт запрос SELECT * FROM имя_таблицы
def get_all_rows(table_name):
    quary = f"SELECT * FROM {table_name}"
    ram = execute_selection_query(quary)
    return ram

# Функиця для удаления всех записей из таблицы
# Создаёт запрос DELETE FROM имя_таблицы
def clean_table(table_name):
    execute_query(f"DELETE FROM {table_name}")

# Функция для вставки новой строки в таблицу
# Принимает список значений для каждой колонки и названия колонок
# Создаёт запрос INSERT INTO имя_таблицы (колонка1, колонка2) VALUES (?, ?)[значение1, значение2]
def insert_row(values):
    columns = "(user_id, subject, level, task, answer, timestamp)"
    sq1_query = f"INSERT INTO {DB_TABLE_USERS_NAME} {columns} VALUES (?, ?, ?, ?, ?, ?)"
    execute_query(sq1_query, values)

# Функция для проверки, есть ли элемент в указанном столбце таблицы
# Создаёт запрос SELECT колонка FROM имя_таблицы WHERE колонка == значение LIMIT 1
def is_value_in_table(table_name, column_name, value):
    sq1_query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} = ?"
    raw = execute_selection_query(sq1_query, [value])
    return raw

# Удалить пользователя по id
def delete_user(user_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, "user_id", user_id):
        sq1_query = f"DELETE FROM {DB_TABLE_USERS_NAME} WHERE user_id = ?"
        execute_query(sq1_query, [user_id])

# Обновить значение в указанной строке и колонки
def update_row_value(user_id, column_name, new_value):
    if is_value_in_table(DB_TABLE_USERS_NAME, "user_id", user_id):
        sq1_query = f"UPDATE {DB_TABLE_USERS_NAME} SET {column_name} = ? WHERE user_id = {user_id}"
        execute_query(sq1_query, [new_value])
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")

# Функция для получения данных для указанного пользователя
def get_data_for_user(user_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, "user_id", user_id):
        sq1_query = (F"SELECT user_id, subject, level, task, answer, timestamp FROM {DB_TABLE_USERS_NAME} "
                     F"WHERE user_id = ? limit 1")
        row = execute_selection_query(sq1_query, [user_id])[0]
        return {"subject": row[1], "level": row[2], "task": row[3], "answer": row[4], "timestamp": row[5]}
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
        return {"subject": "", "level": "", "task": "", "answer": "", "timestamp": ""}

# Функция для подготовки базы данных
# Создаёт/подключается к бд, добавляет все таблицы, заполняет таблицу с промтами
def prepare_db(clean_if_exists=False):
    create_db()
    create_table(DB_TABLE_USERS_NAME)
    if clean_if_exists:
        clean_table(DB_TABLE_USERS_NAME)
