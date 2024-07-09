import requests
from bs4 import BeautifulSoup
import sqlite3


def parse_aircraft_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    name = soup.find('h1').text
    info_box = soup.find('table', {'class': 'infobox'})

    if not info_box:
        return None

    aircraft_info = {'name': name}
    rows = info_box.find_all('tr')
    for row in rows:
        header = row.find('th')
        data = row.find('td')
        if header and data:
            key = header.text.strip()
            value = ' '.join(data.stripped_strings)
            aircraft_info[key] = value

    return aircraft_info


def save_aircraft_to_db(aircraft_info):
    conn = sqlite3.connect('aircrafts.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aircrafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        developer TEXT,
        manufacturer TEXT,
        first_flight TEXT,
        introduction TEXT,
        status TEXT,
        operators TEXT,
        production_years TEXT,
        number_built TEXT
    )
    ''')

    cursor.execute('''
    INSERT INTO aircrafts (
        name, type, developer, manufacturer, first_flight, introduction,
        status, operators, production_years, number_built
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        aircraft_info.get('name'),
        aircraft_info.get('Тип'),
        aircraft_info.get('Разработчик'),
        aircraft_info.get('Производитель'),
        aircraft_info.get('Первый полёт'),
        aircraft_info.get('Начало эксплуатации'),
        aircraft_info.get('Статус'),
        aircraft_info.get('Эксплуатанты'),
        aircraft_info.get('Годы производства'),
        aircraft_info.get('Единиц произведено')
    ))

    conn.commit()
    conn.close()


def add_aircraft(url):
    aircraft_info = parse_aircraft_page(url)
    if aircraft_info:
        save_aircraft_to_db(aircraft_info)
        print(f"Added {aircraft_info['name']} to the database.")
    else:
        print("Failed to parse the aircraft page.")


while True:
    add_aircraft(input())
