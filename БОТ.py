import telebot
from telebot import types
import sqlite3

API_TOKEN = '6870588906:AAESoxC12LH6-oPAbulw70rp3PqMIalm_lc'
bot = telebot.TeleBot(API_TOKEN)


class Aircraft:
    def __init__(self, name):
        self.name = name
        self.attributes = []

    def add_attribute(self, attribute):
        self.attributes.append(attribute)


aircrafts = []


def load_aircrafts():
    conn = sqlite3.connect('aircrafts.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT name, type, developer, manufacturer, first_flight, introduction, status, operators, production_years, number_built FROM aircrafts')
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        name = row[0]
        aircraft = Aircraft(name)
        for attribute in row[1:]:
            if attribute:
                aircraft.add_attribute(attribute)
        aircrafts.append(aircraft)


load_aircrafts()

user_state = {}

question_templates = {
    'type': 'Этот самолёт {}?',
    'developer': 'Этот самолёт разработан {}?',
    'manufacturer': 'Этот самолёт произведен {}?',
    'first_flight': 'Первый полёт этого самолёта был {}?',
    'introduction': 'Этот самолёт был введен в эксплуатацию {}?',
    'status': 'Этот самолёт сейчас {}?',
    'operators': 'Этот самолёт эксплуатируется {}?',
    'production_years': 'Этот самолёт производился {}?',
    'number_built': 'Единиц этого самолёта произведено {}?'
}


def reset_game(chat_id):
    user_state[chat_id] = {
        "state": "start",
        "local_list": list(aircrafts),
        "positive_answers": [],
        "negative_answers": [],
        "current_aircraft": None,
        "current_attribute": None
    }


@bot.message_handler(commands=['start'])
def start_game(message):
    reset_game(message.chat.id)
    bot.send_message(message.chat.id, "Загадай самолёт и нажми /ready")


@bot.message_handler(commands=['ready'])
def ready(message):
    state = user_state.get(message.chat.id, {})
    if state and state.get("state") == "start":
        bot.send_message(message.chat.id, "Начинаю угадывать!")
        ask_question(message)
    else:
        bot.send_message(message.chat.id, "Нажмите /start чтобы начать сначала.")


def ask_question(message):
    state = user_state[message.chat.id]
    local_list = state["local_list"]

    if not local_list:
        bot.send_message(message.chat.id, "Не знаю, что это :( Как называется этот самолёт?")
        state["state"] = "add_aircraft"
        return

    if state["current_aircraft"] is None:
        state["current_aircraft"] = local_list.pop(0)

    current_aircraft = state["current_aircraft"]

    for attribute in current_aircraft.attributes:
        if attribute not in state["positive_answers"] and attribute not in state["negative_answers"]:
            question = generate_question(attribute)
            state["current_attribute"] = attribute
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            button_yes = types.KeyboardButton('Да')
            button_no = types.KeyboardButton('Нет')
            button_unknown = types.KeyboardButton('Не знаю')
            keyboard.add(button_yes, button_no, button_unknown)
            bot.send_message(message.chat.id, question, reply_markup=keyboard)
            return

    bot.send_message(message.chat.id, f"Я угадал! Это {current_aircraft.name}?")
    state["state"] = "guess"
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_yes = types.KeyboardButton('Да')
    button_no = types.KeyboardButton('Нет')
    keyboard.add(button_yes, button_no)
    bot.send_message(message.chat.id, "Правильно?", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    state = user_state.get(message.chat.id, {})
    if not state:
        bot.send_message(message.chat.id, "Нажмите /start чтобы начать игру.")
        return

    if state["state"] == "add_aircraft":
        bot.send_message(message.chat.id, "Пожалуйста, введите название самолёта.")
        state["state"] = "add_aircraft_name"
        bot.register_next_step_handler(message, add_aircraft_name)
        return

    if state["state"] == "guess":
        if message.text.lower() == "да":
            bot.send_message(message.chat.id, "Ура! Сыграем еще? /start", reply_markup=types.ReplyKeyboardRemove())
            reset_game(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Жаль :( Попробую еще раз!", reply_markup=types.ReplyKeyboardRemove())
            state["current_aircraft"] = None
            ask_question(message)
        return

    if state["state"] == "start" and "current_aircraft" in state:
        attribute = state["current_attribute"]
        if message.text.lower() == "да":
            state["positive_answers"].append(attribute)
        elif message.text.lower() == "нет":
            state["negative_answers"].append(attribute)
            state["current_aircraft"] = None  # move to the next aircraft
        else:
            bot.send_message(message.chat.id, "Ответ не распознан. Пожалуйста, ответьте 'Да', 'Нет' или 'Не знаю'.")
            return
        ask_question(message)


def add_aircraft_name(message):
    state = user_state[message.chat.id]
    aircraft_name = message.text
    bot.send_message(message.chat.id, "Введите ключевые слова через запятую.")
    state["new_aircraft_name"] = aircraft_name
    bot.register_next_step_handler(message, add_aircraft_attributes)


def add_aircraft_attributes(message):
    state = user_state[message.chat.id]
    attributes = message.text.split(',')
    aircraft = Aircraft(state["new_aircraft_name"])
    for attribute in attributes:
        aircraft.add_attribute(attribute.strip())
    aircrafts.append(aircraft)
    bot.send_message(message.chat.id, "Спасибо! Я запомнил :) Готов попробовать еще раз! /start",
                     reply_markup=types.ReplyKeyboardRemove())
    reset_game(message.chat.id)


def match_answers(answers, aircraft):
    for answer in answers:
        if answer not in aircraft.attributes:
            return False
    return True


def generate_question(attribute):
    for key, template in question_templates.items():
        if key in attribute.lower():
            return template.format(attribute)
    return f"Это {attribute}?"


@bot.message_handler(commands=['buttons'])
def send_buttons(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_yes = types.KeyboardButton('Да')
    button_no = types.KeyboardButton('Нет')
    button_unknown = types.KeyboardButton('Не знаю')
    keyboard.add(button_yes, button_no, button_unknown)
    bot.send_message(message.chat.id, "Выберите вариант:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text in ['Да', 'Нет', 'Не знаю'])
def handle_button_response(message):
    handle_message(message)


bot.polling()
