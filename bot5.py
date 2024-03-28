import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import time
from config5 import *
from gpt5 import *
from database import *
import logging

# Токен и класс GPT
bot = telebot.TeleBot(BOT_TOKEN)
gpt = GPT()

# Создания таблицы и проверка
prepare_db()
get_all_rows(DB_TABLE_USERS_NAME)

# Выведение ошибок с помощью Logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt", filemode="a",
)

# Функция для создание кнопок
def create_markup(button_labels):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for label in button_labels:
        markup.add(KeyboardButton(label))
    return markup

# debug и история запросов
@bot.message_handler(commands=['debug'])
def debug_command(message):
    with open("log_file.txt", "r", encoding="latin1") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(commands=["history"])
@bot.message_handler(func=lambda message: "История запросов" in message.text)
def command_history(message):
    user_id = message.from_user.id
    history = get_data_for_user(user_id)
    if history:
        history_text = f"{history['timestamp']}:  ({history['task']})  -  ({history['answer']})"
        bot.send_message(message.chat.id, f"Ваша история запросов:\n{history_text}")
    else:
        bot.send_message(message.chat.id, "У вас нет истории запросов.")

# Команда старт
@bot.message_handler(commands=["start"])
def start_command(message):
    user_name, user_id = message.from_user.first_name, message.from_user.id
    if is_value_in_table(DB_TABLE_USERS_NAME, "user_id", user_id):
        delete_user(user_id)
    insert_row([user_id, 'null', 'null', 'null', 'null', "null"])
    bot.send_message(message.chat.id, f"Здравствуй {user_name}! Вас приветствует бот мультипомощник. "
                                                   "Чтобы начать написание своего запроса, ваи необходимо указать "
                                                   "предмет, и затем уровень объяснения. Или можно посмотреть "
                                                   "инструкцию по пользованию бота, или его описание.\n\n"
                                                   "Выберите предмет:",
                   reply_markup=create_markup(["Русский язык", "Математика", "История", "Другие варианты"]))


@bot.message_handler(func=lambda message: "Другие варианты" in message.text)
def other_options(message):
    bot.send_message(message.chat.id, "Другие варианты",
                     reply_markup=create_markup(["Инструкция", "Описание бота", "Вернуться назад"]))


# Другие команды
@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda message: "Инструкция" in message.text)
def help_command(message):
    message_text = message.text
    bot.send_message(message.chat.id,  "Инструкция по использованию бота:\nСначала до написания "
                                       "своего промта нужно ОБЯЗАТЕЛЬНО указать предмет и уровень объяснения. "
                                       "После этого необходимо выбрать уровень объяснения «Новичок» или «Профи»."
                                       "Если вы выберете уровень «Новичок», бот будет объяснять более простыми "
                                       "терминами. А если вы выберете уровень «Профи», уже очевидно, объяснять будет более сложными терминами. "
                                       "После того, как вы отправите свой промт, вам нужно будет подождать некоторое время.",
                     reply_markup=create_markup(["Инструкция", "Описание бота", "Вернуться назад"]))
    if message_text == "/help":
        bot.send_message(message.chat.id, "Клавиатурные кнопки были убраны", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(commands=["about"])
@bot.message_handler(func=lambda message: "Описание бота" in message.text)
def about_command(message):
    message_text = message.text
    bot.send_message(message.chat.id, "Описание бота:\n\nЭтот бот ваш универсальный помощник по трём "
                                      "предметам: русскому языку, математике и истории. ", reply_markup=create_markup(["Инструкция", "Описание бота", "Вернуться назад"]))
    if message_text == "/about":
        bot.send_message(message.chat.id, "Клавиатурные кнопки были убраны", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(commands=["level_beginner", "level_advanced"])
def command_level(mesaage):
    processing_selected_level(mesaage)


@bot.message_handler(commands=["solve_task"])
def solve_task_command(message):
    correct_or_change(message)


@bot.message_handler(commands=['continue_explaining'])
@bot.message_handler(func=lambda message: "Продолжить" in message.text)
def continue_commands(message):
    if (is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null")
            or is_value_in_table(DB_TABLE_USERS_NAME, "level", "null")
            or is_value_in_table(DB_TABLE_USERS_NAME, "task", "null")):
        if is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null"):
            bot.send_message(message.chat.id, "Сначала выберите предмет: ",
                             reply_markup=create_markup(["Русский язык", "Математика", "История"]))
            bot.register_next_step_handler(message, processing_selected_subject)
            return
        elif is_value_in_table(DB_TABLE_USERS_NAME, "level", "null"):
            bot.send_message(message.chat.id, "Сначала выберите уровень объяснения: ",
                             reply_markup=create_markup(["Новичок", "Профи"]))
            bot.register_next_step_handler(message, processing_selected_level)
            return
        else:
            bot.send_message(message.chat.id, "Сначала напишите свой промт: ")
            bot.register_next_step_handler(message, solve_task_command)
            return
    bot.send_message(message.chat.id, "Подождите чутка", reply_markup=ReplyKeyboardRemove())
    get_promt(message)
    return


@bot.message_handler(commands=['end_dialog'])
@bot.message_handler(func=lambda message: "Завершить" in message.text)
def end_task_commands(message):
    if (is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null")
            or is_value_in_table(DB_TABLE_USERS_NAME, "level", "null")
            or is_value_in_table(DB_TABLE_USERS_NAME, "task", "null")):
        if is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null"):
            bot.send_message(message.chat.id, "Сначала выберите предмет: ",
                             reply_markup=create_markup(["Русский язык", "Математика", "История"]))
            bot.register_next_step_handler(message, processing_selected_subject)
            return
        elif is_value_in_table(DB_TABLE_USERS_NAME, "level", "null"):
            bot.send_message(message.chat.id, "Сначала выберите уровень объяснения: ",
                             reply_markup=create_markup(["Новичок", "Профи"]))
            bot.register_next_step_handler(message, processing_selected_level)
            return
        else:
            bot.send_message(message.chat.id, "Сначала напишите свой промт: ")
            bot.register_next_step_handler(message, solve_task_command)
            return
    #time.sleep(2)
    bot.send_message(message.chat.id, "Текущий рассказ завершено, напиши новый рассказ: ",
                     reply_markup=ReplyKeyboardRemove())
    start_command(message)
    return


@bot.message_handler(commands=["help_with_russian_language", "help_with_maths", "help_with_history"])
@bot.message_handler()
def processing_selected_subject(message):
    message_text, user_id = message.text, message.from_user.id
    if message_text == "Русский язык" or message_text == "/help_with_russian_language":
        update_row_value(user_id, "subject", "Russian language")
    elif message_text == "Математика" or message_text == "/help_with_maths":
        update_row_value(user_id, "subject", "maths")
    elif message_text == "История" or message_text == "/help_with_history":
        update_row_value(user_id, "subject", "history")
    elif message_text == "Вернуться назад":
        start_command(message)
        return
    else:
        bot.send_message(message.chat.id, "Я не понял вашего действия, выберите клавиатурную кнопку!")
        return
    bot.send_message(message.chat.id, "А теперь выберите уровень объяснения: ",
                     reply_markup=create_markup(["Новичок", "Профи"]))
    bot.register_next_step_handler(message, processing_selected_level)


def processing_selected_level(message):
    message_text, user_id = message.text, message.from_user.id
    if is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null"):
        bot.send_message(message.chat.id, "Сначала выберите предмет: ",
                         reply_markup=create_markup(["Русский язык", "Математика", "История"]))
        bot.register_next_step_handler(message, processing_selected_subject)
        return
    if message_text == "Новичок" or message_text == "/level_beginner":
        update_row_value(user_id, "level", "beginner")
    elif message_text == "Профи" or message_text == "/level_advanced":
        update_row_value(user_id, "level", "advanced")
    else:
        bot.send_message(message.chat.id, "Я не понял вашего действия, выберите клавиатурную кнопку!")
        return
    res, second_res = get_data_for_user(user_id)['subject'], get_data_for_user(user_id)["level"]
    if res == "Russian language":
        subject = "Русскому языку"
    elif res == "maths":
        subject = "Математика"
    else:
        subject = "История"
    if second_res == "beginner":
        level = "Новичок"
    else:
        level = "Профи"
    bot.send_message(message.chat.id, f"Вы действительно хотите использовать эти параметры?\n\n"
                                      f"({subject}; {level})",
                     reply_markup=create_markup(["Верно", "Изменить"]))
    bot.register_next_step_handler(message, correct_or_change)


def correct_or_change(message):
    message_text, user_id = message.text, message.from_user.id
    if (is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null")
            or is_value_in_table(DB_TABLE_USERS_NAME, "level", "null")):
        if is_value_in_table(DB_TABLE_USERS_NAME, "subject", "null"):
            bot.send_message(message.chat.id, "Сначала выберите предмет: ",
                             reply_markup=create_markup(["Русский язык", "Математика", "История"]))
            bot.register_next_step_handler(message, processing_selected_subject)
            return
        else:
            is_value_in_table(DB_TABLE_USERS_NAME, "level", "null")
            bot.send_message(message.chat.id, "Сначала выберите уровень объяснения: ",
                             reply_markup=create_markup(["Новичок", "Профи"]))
            bot.register_next_step_handler(message, processing_selected_level)
            return
    if message_text == "Верно" or message_text == "/solve_task":
        bot.send_message(message.chat.id, "Ура! теперь можно написать свой промт: ",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_promt)
        return
    else:
        start_command(message)
        return


def get_promt(message):
    message_text, user_id = message.text, message.from_user.id
    if message.content_type != "text":
        bot.send_message(message.chat.id, "Отправь промт текстовым сообщением")
        bot.register_next_step_handler(message, get_promt)
        return
    user_promt = message_text
    if gpt.count_tokens(user_promt) > MAX_TOKENS:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_promt)
        return
    update_row_value(user_id, "task",  user_promt)
    bot.send_message(message.chat.id, "Ответ генерируется. Пожалуйста, подождите некоторое время",
                     reply_markup=ReplyKeyboardRemove())

    formatted_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    update_row_value(user_id, "timestamp", formatted_time_str)

    res, second_res, third_res = (get_data_for_user(user_id),
                                  get_data_for_user(user_id)['subject'], get_data_for_user(user_id)['level'])
    system_prompt = PROMPTS_TEMPLATES[second_res][third_res]
    promt = gpt.make_promt(res, system_prompt)
    resp = gpt.send_request(promt)
    success, answer = gpt.process_resp(resp)
    update_row_value(user_id, "answer", answer)

    bot.send_message(message.chat.id, get_data_for_user(user_id)['answer'],
                     reply_markup=create_markup(["Продолжить", "Завершить", "История запросов"]))


bot.polling()
