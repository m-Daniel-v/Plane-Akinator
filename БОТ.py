import telebot
from telebot import types
import sqlite3


bot = telebot.TeleBot('API_TOKEN')


def load_data(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM aircrafts')
    data = cursor.fetchall()
    conn.close()
    return data


def preprocess_data(data):
    processed_data = []
    for row in data:
        processed_data.append({
            'name': row[1].lower(),
            'classification_role': row[2].lower().split(';') if row[2] else [],
            'subclassification_role': row[3].lower().split(';') if row[3] else [],
            'aerodynamic_balance_scheme': row[4].lower().split(';') if row[4] else [],
            'construction_classification': row[5].lower().split(';') if row[5] else [],
            'engine_type': row[6].lower().split(';') if row[6] else [],
            'flight_range_classification': row[7].lower().split(';') if row[7] else [],
            'number_of_engines': str(row[8]),  # Преобразуем в строку
            'wing_location_classification': row[9].lower().split(';') if row[9] else [],
            'fuselage_type_classification': row[10].lower().split(';') if row[10] else [],
            'chassis_type_classification': row[11].lower().split(';') if row[11] else [],
            'tail_type_and_location_classification': row[12].lower().split(';') if row[12] else [],
            'engine_location_classification': row[13].lower().split(';') if row[13] else []
        })
    return processed_data


def generate_question(classification, column_name):
    questions = {
        'classification_role': 'Это {} самолёт?',
        'subclassification_role': 'Это {}?',
        'aerodynamic_balance_scheme': 'Это самолёт {} по своей аэродинамической балансировочной схеме?',
        'construction_classification': 'Это {}?',
        'engine_type': 'Этот самолёт имеет {} тип двигателя?',
        'flight_range_classification': 'Это самолёт {}?',
        'number_of_engines': 'У него {} двигателей?',
        'wing_location_classification': 'Это {}?',
        'fuselage_type_classification': 'Это {} самолёт?',
        'chassis_type_classification': 'Этот самолёт имеет {} шасси?',
        'tail_type_and_location_classification': 'Этот самолёт имеет {}?',
        'engine_location_classification': 'У этого самолёта двигатели расположены {}?'
    }
    return questions[column_name].format(classification)


db_file = 'aircrafts.db'
data = load_data(db_file)
processed_data = preprocess_data(data)

user_state = {}
new_aircraft_data = {}


# Функция для перезапуска игры
def reset_game(message, restart=False):
    user_id = message.chat.id
    user_state[user_id] = {
        'step': 0,
        'current_data': processed_data,
        'yes_answers': [],
        'no_answers': [],
        'asked_columns': set(),
        'last_question': False
    }
    if user_id in new_aircraft_data:
        new_aircraft_data.pop(user_id)  # Удаляем промежуточные данные о новом самолете
    if restart:
        bot.send_message(user_id,
                         "Игра перезапущена. Давайте начнем угадывать самолёт заново. Отвечайте на вопросы да или нет.")
    ask_question(message)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Добро пожаловать! Давайте начнем угадывать самолёт. Отвечайте на вопросы да или нет.")
    reset_game(message)


# Функция для задания вопроса
def ask_question(message):
    user_id = message.chat.id
    state = user_state[user_id]
    current_data = state['current_data']

    if not current_data:
        bot.send_message(user_id, "Не удалось определить самолёт.")
        request_new_aircraft_data(user_id)
        return

    if len(current_data) == 1 and not state['last_question']:
        bot.send_message(user_id, f"Это {current_data[0]['name'].title()}?")
        state['last_question'] = True
        return

    question_order = [
        'classification_role', 'subclassification_role', 'aerodynamic_balance_scheme',
        'construction_classification', 'engine_type', 'flight_range_classification',
        'number_of_engines', 'wing_location_classification', 'fuselage_type_classification',
        'chassis_type_classification', 'tail_type_and_location_classification',
        'engine_location_classification'
    ]

    for column_key in question_order:
        for aircraft in current_data:
            classifications = aircraft[column_key] if isinstance(aircraft[column_key], list) else [aircraft[column_key]]
            for classification in classifications:
                if (column_key, classification) not in state['yes_answers'] and (column_key, classification) not in \
                        state['no_answers']:
                    question = generate_question(classification, column_key)

                    markup = types.ReplyKeyboardMarkup(row_width=2)
                    markup.add('да', 'нет')
                    restart_button = types.KeyboardButton('Перезапуск')
                    markup.add(restart_button)

                    state['current_classification'] = classification
                    state['current_column'] = column_key
                    state['asked_columns'].add(column_key)

                    bot.send_message(user_id, question, reply_markup=markup)
                    return

    bot.send_message(user_id, "Не удалось определить самолёт.")
    request_new_aircraft_data(user_id)


# Функция для запроса данных о новом самолете
def request_new_aircraft_data(user_id):
    new_aircraft_data[user_id] = {}
    questions = [
        "Пожалуйста, укажите название самолёта:",
        "Классификация по назначению:",
        "Подклассификация по назначению:",
        "Классификация по аэродинамической балансировочной схеме:",
        "Классификация по конструкции:",
        "Классификация по типу двигателя:",
        "Классификация по диапазону полёта:",
        "Количество двигателей:",
        "Классификация по расположению крыльев:",
        "Классификация по типу фюзеляжа:",
        "Классификация по типу шасси:",
        "Классификация по типу и расположению оперения:",
        "Классификация по расположению двигателей:"
    ]
    new_aircraft_data[user_id]['questions'] = questions
    new_aircraft_data[user_id]['answers'] = []
    bot.send_message(user_id, questions[0])


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.chat.id

    if user_id not in user_state and user_id not in new_aircraft_data:
        bot.send_message(user_id, "Нажмите /start.")
        return

    if message.text.lower() == 'перезапуск':
        reset_game(message, restart=True)
        return

    if user_id in new_aircraft_data:
        state = new_aircraft_data[user_id]
        state['answers'].append(message.text.strip())

        if len(state['answers']) < len(state['questions']):
            bot.send_message(user_id, state['questions'][len(state['answers'])])
        else:
            save_new_aircraft_data(state['answers'])
            bot.send_message(user_id, "Спасибо! Ваши данные сохранены.")
            new_aircraft_data.pop(user_id)
        return

    state = user_state[user_id]

    if 'current_classification' not in state:
        bot.send_message(user_id, "Нажмите /start.")
        return

    answer = message.text.strip().lower()
    classification = state['current_classification']
    column_key = state['current_column']

    if answer == 'да':
        if state['last_question']:
            bot.send_message(user_id, f"Ура, я угадал! Вы загадали самолёт: {state['current_data'][0]['name'].title()}")
            user_state.pop(user_id)
            return
        state['yes_answers'].append((column_key, classification))
        state['current_data'] = [entry for entry in state['current_data'] if classification in entry[column_key]]
    elif answer == 'нет':
        if state['last_question']:
            bot.send_message(user_id, "Не удалось определить самолёт.")
            request_new_aircraft_data(user_id)
            user_state.pop(user_id)
            return
        state['no_answers'].append((column_key, classification))
        state['current_data'] = [entry for entry in state['current_data'] if classification not in entry[column_key]]
        state['asked_columns'].discard(column_key)  # Удаляем колонку из списка заданных вопросов, если ответ был "нет"

    if len(state['current_data']) == 1 and not state['last_question']:
        bot.send_message(user_id, f"Это {state['current_data'][0]['name'].title()}?")
        state['last_question'] = True
        return
    elif len(state['current_data']) == 0:
        bot.send_message(user_id, "Не удалось определить самолёт.")
        request_new_aircraft_data(user_id)
        user_state.pop(user_id)
        return

    ask_question(message)


# Функция для сохранения новых данных о самолете
def save_new_aircraft_data(answers):
    conn = sqlite3.connect('aircrafts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO aircrafts (
            name, classification_role, subclassification_role, aerodynamic_balance_scheme,
            construction_classification, engine_type, flight_range_classification,
            number_of_engines, wing_location_classification, fuselage_type_classification,
            chassis_type_classification, tail_type_and_location_classification,
            engine_location_classification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', answers)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)
