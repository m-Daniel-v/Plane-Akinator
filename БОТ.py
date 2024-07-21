import telebot
from telebot import types
import sqlite3


bot = telebot.TeleBot('6754617208:AAHyxtRbD43fFGaBXhwbvD0iKvgpOrLdZvY')


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
            'first_flight_year': row[2],
            'classification_role': row[3].lower().split(';') if row[3] else [],
            'subclassification_role': row[4].lower().split(';') if row[4] else [],
            'aerodynamic_balance_scheme': row[5].lower().split(';') if row[5] else [],
            'construction_classification': row[6].lower().split(';') if row[6] else [],
            'engine_type': row[7].lower().split(';') if row[7] else [],
            'flight_range_classification': row[8].lower().split(';') if row[8] else [],
            'number_of_engines': str(row[9]) if row[9] else '',
            'wing_location_classification': row[10].lower().split(';') if row[10] else [],
            'fuselage_type_classification': row[11].lower().split(';') if row[11] else [],
            'chassis_type_classification': row[12].lower().split(';') if row[12] else [],
            'tail_type_and_location_classification': row[13].lower().split(';') if row[13] else [],
            'engine_location_classification': row[14].lower().split(';') if row[14] else []
        })
    return processed_data


# Функция для генерации вопросов на основе классификаций
def generate_question(classification, column_name):
    questions = {
        'first_flight_year': 'Этот самолёт совершил свой первый полёт в {}-е годы?',
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


# Загрузка данных из базы данных
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
        'skip_columns': set(),
        'asked_columns': set(),
        'last_question': False,
        'decade_question_asked': False,
        'current_decade_index': 0,
        'aircraft_index': 0  # Индекс для отслеживания текущего самолёта при вопросе о названии
    }
    if user_id in new_aircraft_data:
        new_aircraft_data.pop(user_id)  # Удаляем промежуточные данные о новом самолете
    if restart:
        bot.send_message(user_id,
                         "Игра перезапущена. Давайте начнем угадывать самолёт заново. Отвечайте на вопросы да, нет или не знаю.")
    ask_question(message)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    bot.send_message(user_id,
                     "Добро пожаловать! Давайте начнем угадывать самолёт. Отвечайте на вопросы да, нет или не знаю.")
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

    if not state['decade_question_asked']:
        decades = sorted(set([int(str(aircraft['first_flight_year'])[:3] + '0') for aircraft in current_data if
                              aircraft['first_flight_year'] is not None]))
        if state['current_decade_index'] < len(decades):
            decade = decades[state['current_decade_index']]
            question = generate_question(decade, 'first_flight_year')
            markup = types.ReplyKeyboardMarkup(row_width=3)
            markup.add('да', 'нет', 'не знаю')
            restart_button = types.KeyboardButton('Перезапуск')
            markup.add(restart_button)

            state['current_classification'] = decade
            state['current_column'] = 'first_flight_year'
            state['asked_columns'].add('first_flight_year')

            bot.send_message(user_id, question, reply_markup=markup)
            state['decade_question_asked'] = True
            return

    question_order = [
        'classification_role', 'subclassification_role', 'aerodynamic_balance_scheme',
        'construction_classification', 'engine_type', 'flight_range_classification',
        'number_of_engines', 'wing_location_classification', 'fuselage_type_classification',
        'chassis_type_classification', 'tail_type_and_location_classification',
        'engine_location_classification'
    ]

    for column_key in question_order:
        if column_key in state['skip_columns']:
            continue
        for aircraft in current_data:
            classifications = aircraft[column_key] if isinstance(aircraft[column_key], list) else [aircraft[column_key]]
            for classification in classifications:
                if (column_key, classification) not in state['yes_answers'] and (column_key, classification) not in \
                        state['no_answers']:
                    question = generate_question(classification, column_key)

                    markup = types.ReplyKeyboardMarkup(row_width=3)
                    markup.add('да', 'нет', 'не знаю')
                    restart_button = types.KeyboardButton('Перезапуск')
                    markup.add(restart_button)

                    state['current_classification'] = classification
                    state['current_column'] = column_key
                    state['asked_columns'].add(column_key)

                    bot.send_message(user_id, question, reply_markup=markup)
                    return

    if len(current_data) == 1 or state['aircraft_index'] < len(current_data):
        if state['aircraft_index'] < len(current_data):
            bot.send_message(user_id, f"Это {current_data[state['aircraft_index']]['name'].title()}?")
            state['last_question'] = True
            state['aircraft_index'] += 1
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
            bot.send_message(user_id, f"Ура, я угадал! Вы загадали самолёт: {state['current_data'][state['aircraft_index'] - 1]['name'].title()}")
            user_state.pop(user_id)
            return
        state['yes_answers'].append((column_key, classification))
        if column_key == 'first_flight_year':
            state['current_data'] = [entry for entry in state['current_data'] if entry[column_key] is not None and int(str(entry[column_key])[:3] + '0') == classification]
            state['decade_question_asked'] = True
        else:
            state['current_data'] = [entry for entry in state['current_data'] if classification in entry[column_key]]
    elif answer == 'нет':
        if state['last_question']:
            if state['aircraft_index'] < len(state['current_data']):
                bot.send_message(user_id, f"Это {state['current_data'][state['aircraft_index']]['name'].title()}?")
                state['aircraft_index'] += 1
                return
            else:
                bot.send_message(user_id, "Не удалось определить самолёт.")
                request_new_aircraft_data(user_id)
                user_state.pop(user_id)
                return
        state['no_answers'].append((column_key, classification))
        if column_key == 'first_flight_year':
            state['current_data'] = [entry for entry in state['current_data'] if entry[column_key] is None or int(str(entry[column_key])[:3] + '0') != classification]
            state['current_decade_index'] += 1
            state['decade_question_asked'] = False
        else:
            state['current_data'] = [entry for entry in state['current_data'] if classification not in entry[column_key]]
        state['asked_columns'].discard(column_key)
    elif answer == 'не знаю':
        state['skip_columns'].add(column_key)
        state['asked_columns'].discard(column_key)
        if column_key == 'first_flight_year':
            state['decade_question_asked'] = True  # Пропускаем столбец с датами и переходим к угадыванию классификации

    if len(state['current_data']) == 1 and not state['last_question']:
        bot.send_message(user_id, f"Это {state['current_data'][0]['name'].title()}?")
        state['last_question'] = True
        state['aircraft_index'] = 1  # Сразу задаем вопрос о первом самолете
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
            name, first_flight_year, classification_role, subclassification_role, aerodynamic_balance_scheme,
            construction_classification, engine_type, flight_range_classification,
            number_of_engines, wing_location_classification, fuselage_type_classification,
            chassis_type_classification, tail_type_and_location_classification,
            engine_location_classification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', answers)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)
