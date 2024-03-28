import sqlite3

DB_NAME = 'sqlite.db'
DB_TABLE_USERS_NAME = 'prompts'


def create_db(database_name=DB_NAME):
    db_path = f'{database_name}'
    connection = sqlite3.connect(db_path)
    connection.close()


def execute_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()


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


def create_table(table_name):
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name} ' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'role TEXT, ' \
                f'content TEXT, ' \
                f'date DATETIME, ' \
                f'tokens INTEGER, ' \
                f'session_id INTEGER DEFAULT 0)'
    execute_query(sql_query)


def get_all_rows(table_name):
    rows = execute_selection_query(f'''SELECT * FROM {table_name}''')
    for row in rows:
        print(row)


def clean_table(table_name):
    delete_table = f'''DELETE FROM {table_name};'''
    execute_query(delete_table)


def insert_row(values):
    columns = '(user_id, role, content, date, tokens, session_id)'
    sql_query = f'''INSERT INTO {DB_TABLE_USERS_NAME} {columns} VALUES (?, ?, ?, ?, ?, ?)'''
    execute_query(sql_query, values)


def is_value_in_table(table_name, column_name, value):
    check = f'''SELECT {column_name} FROM {table_name} WHERE {column_name} = ? LIMIT 1'''
    rows = execute_selection_query(check, (value,))
    return rows


def distinct_data():
    sql_query = f'''SELECT DISTINCT user_id FROM {DB_TABLE_USERS_NAME}'''
    return execute_selection_query(sql_query)


def get_data_for_user(user_id, column_name, column_name1, value):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        receive = f'''SELECT {column_name} FROM {DB_TABLE_USERS_NAME} WHERE {column_name1} = ? ORDER BY date DESC 
        LIMIT 1'''
        return execute_selection_query(receive, (value,))


def get_tokens(user_id, session_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        receive = f'''SELECT tokens FROM {DB_TABLE_USERS_NAME} WHERE user_id = ? and session_id = ? ORDER BY date 
        DESC LIMIT 3'''
        return execute_selection_query(receive, (user_id, session_id, ))


def get_dialogue_for_user(user_id, session_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        sql_query = f'''SELECT content FROM {DB_TABLE_USERS_NAME}
         WHERE user_id = ? AND tokens IS NOT NULL AND session_id = ?
         ORDER BY date ASC'''
        return execute_selection_query(sql_query, (user_id, session_id, ))


def get_size_of_session(user_id, session_id):  # получить количество токенов в указанной сессии
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        sql_query = f'''SELECT tokens FROM {DB_TABLE_USERS_NAME} 
        WHERE user_id = ? AND session_id = ? 
        ORDER BY date DESC LIMIT 1'''
        return execute_selection_query(sql_query, (user_id, session_id,))


def prepare_db(clean_if_exists=False):
    create_db()
    create_table(DB_TABLE_USERS_NAME)
    if clean_if_exists:
        clean_table(DB_TABLE_USERS_NAME)


create_table(table_name=DB_TABLE_USERS_NAME)
