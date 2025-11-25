#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import requests
import mysql.connector
from datetime import datetime, timezone
import pytz

# Lataa API-avain
load_dotenv("KEY.env")
API_KEY = os.getenv("API_KEY")

CITY = "Seinäjoki"
URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# MySQL-yhteys
conn = mysql.connector.connect(
    host='localhost',
    user='esimerkkikäyttäjä',
    password='1234',
    database='weather_db'
)
cursor = conn.cursor()

# Luo taulu, jos ei ole (huom: sarakkeet vastaavat MySQL-taulusi rakennetta)
cursor.execute('''
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paikkakunta VARCHAR(50),
    lämpötila FLOAT,
    sää VARCHAR(100),
    timestamp DATETIME,
    paikallinen_aika DATETIME
)
''')

# Hae säädata
response = requests.get(URL, timeout=10)
response.raise_for_status()
data = response.json()

temp = float(data['main']['temp'])
desc = data['weather'][0]['description']

# Aikaleimat
utc_time = datetime.now(timezone.utc).replace(tzinfo=None)
helsinki_tz = pytz.timezone('Europe/Helsinki')
local_time = datetime.now(helsinki_tz).replace(tzinfo=None)

municipality = CITY

# Tallenna tietokantaan
cursor.execute("""
INSERT INTO weather_data (paikkakunta, lämpötila, sää, timestamp, paikallinen_aika)
VALUES (%s, %s, %s, %s, %s)
""", (municipality, temp, desc, utc_time, local_time))

conn.commit()
cursor.close()
conn.close()

print(f'Data tallennettu: {CITY} {temp}°C {desc} (UTC: {utc_time}, Paikallinen: {local_time})')

