import pandas as pd
import sqlite3
import os


file_path = os.path.join(os.path.dirname(__file__), 'Акинатор.xlsx')


akinator_data = pd.read_excel(file_path)


def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aircrafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            classification_role TEXT,
            subclassification_role TEXT,
            aerodynamic_balance_scheme TEXT,
            construction_classification TEXT,
            engine_type TEXT,
            flight_range_classification TEXT,
            number_of_engines INTEGER,
            wing_location_classification TEXT,
            fuselage_type_classification TEXT,
            chassis_type_classification TEXT,
            tail_type_and_location_classification TEXT,
            engine_location_classification TEXT
        );
    ''')
    conn.commit()
    return conn


def save_to_db(conn, aircrafts):
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO aircrafts (
            name, classification_role, subclassification_role, aerodynamic_balance_scheme,
            construction_classification, engine_type, flight_range_classification,
            number_of_engines, wing_location_classification, fuselage_type_classification,
            chassis_type_classification, tail_type_and_location_classification,
            engine_location_classification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', aircrafts)
    conn.commit()

# Преобразование данных в нижний регистр и формирование списка
aircraft_records = []
for index, row in akinator_data.iterrows():
    record = (
        row['Самолёт'].lower(),
        row['Классификация по назначению'].lower() if pd.notnull(row['Классификация по назначению']) else '',
        row['Подклассификация по назначению'].lower() if pd.notnull(row['Подклассификация по назначению']) else '',
        row['Классификация по аэродинамической балансировочной схеме'].lower() if pd.notnull(row['Классификация по аэродинамической балансировочной схеме']) else '',
        row['Классификация по конструкции'].lower() if pd.notnull(row['Классификация по конструкции']) else '',
        row['Классификация по типу двигателя'].lower() if pd.notnull(row['Классификация по типу двигателя']) else '',
        row['Классификация по диапазону полёта'].lower() if pd.notnull(row['Классификация по диапазону полёта']) else '',
        int(row['Количество двигателей']) if pd.notnull(row['Количество двигателей']) else 0,
        row['Классификация по расположению крыльев'].lower() if pd.notnull(row['Классификация по расположению крыльев']) else '',
        row['Классификация по типу фюзеляжа'].lower() if pd.notnull(row['Классификация по типу фюзеляжа']) else '',
        row['Классификация по типу шасси'].lower() if pd.notnull(row['Классификация по типу шасси']) else '',
        row['Классификация по типу и расположению оперения'].lower() if pd.notnull(row['Классификация по типу и расположению оперения']) else '',
        row['Классификация по расположению двигателей'].lower() if pd.notnull(row['Классификация по расположению двигателей']) else ''
    )
    aircraft_records.append(record)


db_conn = create_connection('aircrafts.db')
save_to_db(db_conn, aircraft_records)
db_conn.close()
