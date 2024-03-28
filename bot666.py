import telebot
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from telebot import types
import datetime
from gpt666 import *
from limitation666 import *

bot = TeleBot(TOKEN)

# Логгирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


@bot.message_handler(commands=['debug'])
def send_logs(message):
    try:
        with open("log_file.txt", "rb") as f:
            bot.send_document(message.chat.id, f)
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(message.chat.id, "Простите, но я не могу предоставить вам логи, так как их нет.")


#Словари и списки
genres = ['Комедия', 'Приключения', 'Мистика']
main_characters = ['Буратино', 'Копатыч', 'Шерлок Хомс', 'Мисс Марпл', 'Чудо-женщина', 'Гарри Поттер']
settings = ['Фэнтези средневековый мир', 'Колониальный Марс', 'Волшебный магазин "Пятерочка"']

user_data = {}


# Непосредственно сам бот
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def commands(message):
    user_id = message.from_user.id
    if message.text == '/start':
        user_data[user_id] = {
            'genre': None,
            'character': None,
            'setting': None,
            'info': None,
            'state': None,
            'test_mode': None,
            'session_id': 0
        }

        create_db()
        logging.info('Создали бд')

        create_table(DB_TABLE_USERS_NAME)
        logging.info('Создали таблицу если ее нет')

        name_user = message.from_user.first_name
        logging.info("Отправка приветственного сообщения")
        bot.send_message(message.chat.id, text=f"Привет, {name_user}\n"
                                               f"Я бот-сценарист, который может помочь с созданием уникальных и "
                                               f"интересных историй. Напиши /new_story чтобы создать новую историю. "
                                               f"Чтобы закончить пиши /end.",
                         reply_markup=create_keyboard(['/new_story']))

    if message.text == '/help':
        logging.info("Отправка помощи")
        bot.send_message(message.chat.id, text='Запустите бот командой /start\n'
                                               'Начните новую историю командой /new_story.\n'
                                               'Выберите жанр/главного героя/сеттинг.\b'
                                               'Подождите пока история сгенерируется.\n'
                                               'Напишите сообщение связанное с историей, а я продолжу историю учитывая ваше сообщение)',
                         reply_markup=create_keyboard(['/new_story']))


# История
@bot.message_handler(commands=['new_story'])
def story(message):
    user_id = message.from_user.id
    date = datetime.datetime.now()

    logging.info('Новая история')
    if is_limit_users():
        logging.info('количество пользователей превышено')
        bot.send_message(message.chat.id, "Извините, но количество пользователей превышено. Бот недоступен.")
        return

    if not is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        logging.info('Создали таблицу, если пользователя нет')
        value = [user_id, '', '', date, 0, 0]
        insert_row(value)

    session_id = get_data_for_user(user_id, 'session_id', 'user_id', user_id)[0][0]
    session_id += 1
    logging.info('Каждый раз когда пользователь будет вводить команду /new_story сессии будут прибавляться')

    try:
        user_data[user_id]['session_id'] = session_id
        logging.info(f'Запомнили кол-во сессий в словарь: session_id = {session_id}')

        if is_limit_sessions_id(user_id):
            logging.info('Проверяем лимит сессий')
            if session_id == MAX_SESSIONS - 1:
                bot.send_message(message.chat.id, "Осталась 1 доступная сессия")
                logging.info("Сообщили о том, что сессии заканчиваются")
            else:
                logging.info("Сообщили о том, что сессии закончились")
                bot.send_message(message.chat.id, "Извините, но у вас закончились доступные сессии. Бот недоступен")
                return
    except TypeError:
        pass

    try:
        user_data[user_id]['state'] = "в истории"

        bot.send_message(message.chat.id, text='Хорошо, давайте начнем! Какой жанр истории вы бы хотели?',
                         reply_markup=create_keyboard(genres))
        bot.register_next_step_handler(message, choose_genre)

    except KeyError:
        logging.info('Если пользователь не ввел команду /start')
        bot.send_message(message.chat.id, text="Чтобы начать введите команду /start",
                         reply_markup=create_keyboard(['/start']))


def choose_genre(message):
    user_id = message.from_user.id
    genre = message.text

    if genre not in genres:
        logging.info('Пользователь ввел не жанр')
        bot.send_message(message.chat.id, text="Пожалуйста выберите один из предложенных вариантов",
                         reply_markup=create_keyboard(genres))
        bot.register_next_step_handler(message, choose_genre)
        return

    user_data[user_id]['genre'] = genre
    logging.info('Сохранили жанр в словарь')

    bot.send_message(message.chat.id, text='Хорошо, выберите главного героя',
                     reply_markup=create_keyboard(main_characters))
    bot.register_next_step_handler(message, choose_characters)


def choose_characters(message):
    user_id = message.from_user.id
    character = message.text

    if character not in main_characters:
        logging.info('Пользователь ввел не персонажа')
        bot.send_message(message.chat.id, text="Пожалуйста выберите один из предложенных вариантов",
                         reply_markup=create_keyboard(main_characters))
        bot.register_next_step_handler(message, choose_characters)
        return

    user_data[user_id]['character'] = character
    logging.info('Сохранили персонажа в словарь')

    bot.send_message(message.chat.id, text='Отличный выбор, выберите сеттинг:\n'
                                           '1) Фэнтези средневековый мир - огромное королевство с магией.\n'
                                           '2) Колониальный Марс - люди колонизировали Марс и построили там города.\n'
                                           '3) Волшебный магазин "Пятерочка" - место, где можно найти все, что угодно.',
                     reply_markup=create_keyboard(settings))
    bot.register_next_step_handler(message, choose_setting)


def choose_setting(message):
    user_id = message.from_user.id
    setting = message.text

    if setting not in settings:
        logging.info('Пользователь ввел не сеттинг')
        bot.send_message(message.chat.id, text="Пожалуйста выберите один из предложенных вариантов",
                         reply_markup=create_keyboard(settings))
        bot.register_next_step_handler(message, choose_setting)
        return

    user_data[user_id]['setting'] = setting
    logging.info('Сохранили сеттинг в словарь')

    bot.send_message(message.chat.id, text="Супер! Получится крутая история, а чтобы она получилась еще круче можешь "
                                           "написать дополнительную информацию. Если хочешь уже начать пиши /begin",
                     reply_markup=create_keyboard(['/begin']))
    bot.register_next_step_handler(message, add_info)


def add_info(message):
    user_id = message.from_user.id
    info = message.text

    if info != '/begin':
        if not info:
            logging.info("Проверка на текстовое сообщение")
            bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение.")
            bot.register_next_step_handler(message, add_info)
            return

        logging.info('Пользователь ввел доп инфо')
        collection = [{'role': 'info', 'content': info}]
        tokens_info = count_tokens_in_dialogue(collection)

        if is_limit_tokens(user_id, tokens_info):
            logging.info('Проверили на лимит токенов')
            bot.send_message(message.chat.id, "Ваше сообщение превышает лимит. Пожалуйста сократите сообщение и "
                                              "отправьте еще раз.")
            bot.register_next_step_handler(message, add_info)

        user_data[user_id]['info'] = info
        logging.info('Сохранили доп. инфо. в словарь')
        bot.send_message(message.chat.id, text='Отлично, вся информация будет учтена в истории. Чтобы начать введите '
                                               '/begin',
                         reply_markup=create_keyboard(['/begin']))
        return
    else:
        begin_story(message)


@bot.message_handler(commands=['begin'])
def begin_story(message):
    user_id = message.from_user.id

    try:
        if not user_data[user_id]['state']:
            logging.info("Пользователь не нажимал команду /new_story")
            bot.send_message(message.chat.id, text="Чтобы начать новую историю введите команду /new_story, и "
                                                   "пройдите опрос.",
                             reply_markup=create_keyboard(['/new_story']))
            return

        elif not user_data[user_id]['genre']:
            logging.info("не выбрали жанр")
            bot.send_message(message.chat.id, text="Кажется, вы не выбрали жанр, пожалуйста выберите один из "
                                                   "предложенных вариантов.",
                             reply_markup=create_keyboard(genres))
            bot.register_next_step_handler(message, choose_genre)
            return

        elif not user_data[user_id]['character']:
            logging.info('не выбрали героя')
            bot.send_message(message.chat.id, text="Кажется, вы не выбрали героя, пожалуйста выберите один из "
                                                   "предложенных вариантов.",
                             reply_markup=create_keyboard(main_characters))
            bot.register_next_step_handler(message, choose_characters)
            return

        elif not user_data[user_id]['setting']:
            logging.info('не выбрали сеттинг')
            bot.send_message(message.chat.id, text="Кажется, вы не выбрали сеттинг, пожалуйста выберите один из "
                                                   "предложенных вариантов.",
                             reply_markup=create_keyboard(settings))
            bot.register_next_step_handler(message, choose_setting)
            return

        user_data[user_id]['state'] = "начало истории"
    except KeyError:
        logging.info('Пользователь не вводил команду /start')
        bot.send_message(message.chat.id, text="Чтобы начать введите команду /start",
                         reply_markup=create_keyboard(['/start']))
        return



    get_story(message)


#Создание_истории
def get_story(message: types.Message):
    user_id = message.from_user.id
    time = datetime.datetime.now()

    session_id = user_data[user_id]['session_id']
    logging.info('Взяли из словаря кол-во сессий')

    prompt = create_prompt(user_data, user_id)
    logging.info('Взяли промт')

    if user_data[user_id]['state'] == 'продолжение от пользователя':
        logging.info('Если пользователь продолжил, добавляем в промт его продолжение')
        user_prompt = get_data_for_user(user_id, 'content', 'role', 'user')[0][0]
        gpt_prompt = get_data_for_user(user_id, 'content', 'role', 'assistant')[0][0]
        prompt += f'{gpt_prompt}  {user_prompt} - {CONTINUE_STORY}'

    collection = [{'role': 'system', 'content': prompt}]
    tokens_system = count_tokens_in_dialogue(collection)
    logging.info('Узнали кол-во токенов промта')

    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        if user_data[user_id]['state'] == 'продолжение от пользователя':
            logging.info('Считаем все токены')
            tokens = get_tokens(user_id, session_id)
            tokens1 = tokens[0][0]
            tokens2 = tokens[1][0]
            tokens3 = tokens[2][0]
            token = tokens1 + tokens2 + tokens3

            if is_limit_tokens_in_session(user_id, token):
                logging.info('Если токены превышают')
                bot.send_message(message.chat.id, 'Извините, но токены в данной сессии закончились. Чтобы начать новую '
                                                  'историю введите команду /new_story',
                                 reply_markup=create_keyboard(['/new_story']))
                return

    bot.send_message(message.chat.id, "Генерирую...")

    values = [user_id, 'system', prompt, time, tokens_system, session_id]
    insert_row(values)
    logging.info('Добавили промт в таблицу')

    gpt_text = ask_gpt(collection)
    logging.info('Получили ответ от gpt')
    collection.append({'role': 'assistant', 'content': gpt_text})
    tokens_assistant = count_tokens_in_dialogue(collection)

    values = [user_id, 'assistant', gpt_text, time, tokens_assistant, session_id]
    insert_row(values)
    logging.info('Добавили в таблицу ответ от gpt')

    bot.send_message(message.chat.id, gpt_text, reply_markup=create_keyboard(['Конец']))


@bot.message_handler(content_types=['text'])
def continuation(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text
    time = datetime.datetime.now()

    try:
        if not user_data[user_id]['state']:
            logging.info("Пользователь не нажимал команду /new_story")
            bot.send_message(message.chat.id, text="Чтобы начать новую историю введите команду /new_story, и "
                                                   "пройдите опрос.",
                             reply_markup=create_keyboard(['/new_story']))
    except KeyError:
        bot.send_message(message.chat.id, text="Чтобы начать введите команду /start",
                         reply_markup=create_keyboard(['/start']))

    if not user_message:
        logging.info("Проверка на текстовое сообщение")
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение.")
        bot.register_next_step_handler(message, continuation)
        return

    session_id = user_data[user_id]['session_id']
    logging.info('Получили сессии')

    collection = [{'role': 'user', 'content': user_message}]

    if message.text == 'Конец':
        user_data[user_id]['state'] = 'конец'

        logging.info('Пользователь заканчивает историю')
        user_message = END_STORY
        tokens_user = count_tokens_in_dialogue(collection)
        values = [user_id, 'user', user_message, time, tokens_user, session_id]
        insert_row(values)
        logging.info('Сохранили в таблицу сообщение от пользователя 2')

        gpt_prompt = get_data_for_user(user_id, 'content', 'role', 'assistant')[0][0]
        prompt = (f'{create_prompt(user_data, user_id)}\n'
                  f'{gpt_prompt} {user_message}')
        logging.info('Создали новый промт для конца истории')

        collection = [{'role': 'system', 'content': prompt}]
        tokens_system = count_tokens_in_dialogue(collection)
        bot.send_message(message.chat.id, "Генерирую...")
        values = [user_id, 'system', prompt, time, tokens_system, session_id]
        insert_row(values)
        logging.info('Записали в таблицу промт')

        result_for_test = ask_gpt(collection)
        logging.info('получили текст от gpt 2')
        collection.append({'role': 'assistant', 'content': result_for_test})
        tokens_assistant = count_tokens_in_dialogue(collection)
        values = [user_id, 'assistant', result_for_test, time, tokens_assistant, session_id]
        insert_row(values)
        logging.info('записали в таблицу текст от gpt')

        bot.send_message(message.chat.id, result_for_test)

        bot.send_message(message.chat.id, 'Чтобы выйти введите команду /end',
                         reply_markup=create_keyboard(['/end']))
        bot.register_next_step_handler(message, end)
        return

    tokens_user = count_tokens_in_dialogue(collection)

    if is_limit_tokens(user_id, tokens_user):
        logging.info('Пользователь написал длинное сообщение')
        bot.send_message(message.chat.id, text='Ваше сообщение превышает лимит. Пожалуйста сократите сообщение и '
                                               'отправьте еще раз.')
        bot.register_next_step_handler(message, continuation)
        return

    values = [user_id, 'user', user_message, time, tokens_user, session_id]
    insert_row(values)
    logging.info('Записали сообщение от юзера в таблицу')

    try:
        user_data[user_id]['state'] = 'продолжение от пользователя'
    except KeyError:
        bot.send_message(message.chat.id, text="Чтобы начать введите команду /start",
                         reply_markup=create_keyboard(['/start']))

    get_story(message)


# Конец
@bot.message_handler(commands=['end'])
def end(message):
    logging.info('Перешли к концу')
    user_id = message.from_user.id
    try:
        if user_data[user_id]['state'] != 'конец':
            bot.send_message(message.chat.id,
                             text="Кажется, вы еще не начали историю. Чтобы начать введи команду /begin",
                             reply_markup=create_keyboard(['/begin']))
            return
    except KeyError:
        bot.send_message(message.chat.id, text="Чтобы начать введите команду /start",
                         reply_markup=create_keyboard(['/start']))
        return

    bot.send_message(message.chat.id, text="У нас получилась замечательная история. Приходи еще!",
                     reply_markup=create_keyboard(['/new_story']))


# Другое
@bot.message_handler(commands=['clean_table'])
def clean(message):
    clean_table(DB_TABLE_USERS_NAME)
    bot.send_message(message.chat.id, "Таблица успешно очищена")
    logging.info('Таблица успешно очищена')


bot.infinity_polling()
