#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import signal
import time
from typing import Optional
from datetime import datetime

import paho.mqtt.client as mqtt
from mysql.connector import pooling, Error

# --- Konfiguraatio ---
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "chat/messages")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "mqtt_chat"),
}

# --- Lokitus ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mqtt_logger")

db_pool: Optional[pooling.MySQLConnectionPool] = None

def init_db_pool(retries: int = 12, delay_sec: float = 5.0) -> pooling.MySQLConnectionPool:
    last_err = None
    for attempt in range(retries):
        try:
            pool = pooling.MySQLConnectionPool(pool_name="mqtt_pool", pool_size=5, **DB_CONFIG)
            logger.info("Tietokantapooli alustettu")
            return pool
        except Error as err:
            last_err = err
            logger.error(f"Tietokantapoolin luonti epäonnistui (yritys {attempt+1}/{retries}): {err}")
            time.sleep(delay_sec)
    raise RuntimeError(f"MySQL-yhteys ei muodostunut ajoissa: {last_err}")

def save_message(nickname: str, message: str, client_id: Optional[str]) -> None:
    conn = None
    cursor = None
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (nickname, message, created_at, client_id) VALUES (%s, %s, %s, %s)",
            (nickname, message, datetime.utcnow(), client_id),
        )
        conn.commit()
        short = (message[:97] + "...") if len(message) > 100 else message
        logger.info(f"Tallennettu: [{nickname}] {short}")
    except Error as err:
        logger.error(f"Tietokantavirhe INSERTissä: {err}")
    except Exception as e:
        logger.exception(f"Odottamaton virhe tallennuksessa: {e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass

def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Yhdistetty MQTT-brokeriin")
        try:
            client.subscribe(MQTT_TOPIC)
            logger.info(f"Tilattu: {MQTT_TOPIC}")
        except Exception as e:
            logger.error(f"Tilauksen luonti epäonnistui topicille '{MQTT_TOPIC}': {e}")
    else:
        logger.error(f"MQTT-yhteysvirhe, koodi: {rc}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    try:
        payload_str = msg.payload.decode("utf-8", errors="replace").strip()
        logger.info(f"Vastaanotettu viesti topicista {msg.topic}: {payload_str[:100]}")

        nickname = "Tuntematon"
        message_text = ""
        client_id = ""

        try:
            data = json.loads(payload_str)
            nickname = (data.get("nickname") or nickname)[:50]
            message_text = data.get("message") or data.get("text") or ""
            client_id = (data.get("clientId") or data.get("client_id") or "")[:100]
        except json.JSONDecodeError:
            if ": " in payload_str:
                nickname, message_text = payload_str.split(": ", 1)
                nickname = nickname[:50]
            else:
                message_text = payload_str

        if not message_text:
            logger.warning(f"Tyhjä viesti, ei tallenneta: {payload_str}")
            return

        save_message(nickname, message_text, client_id or None)

    except Exception as e:
        logger.exception(f"Virhe viestin käsittelyssä: {e}")

_shutdown = False
def _handle_signal(signum, frame):
    global _shutdown
    if not _shutdown:
        _shutdown = True
        logger.info(f"Saatiin signaali {signum}, pysäytetään MQTT-looppi...")

def main():
    global db_pool
    db_pool = init_db_pool(retries=12, delay_sec=5.0)

    client = mqtt.Client(client_id="mqtt_logger", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        logger.error(f"MQTT-yhteyden avaus epäonnistui {MQTT_BROKER}:{MQTT_PORT}: {e}")
        raise

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("MQTT Logger käynnissä...")
    try:
        client.loop_start()
        while not _shutdown:
            time.sleep(0.2)
    finally:
        try: client.loop_stop()
while not _shutdown:
            time.sleep(0.2)
    finally:
        try: client.loop_stop()
        except Exception: pass
        try: client.disconnect()
        except Exception: pass
        logger.info("MQTT Logger sammutettu.")

if __name__ == "__main__":
    main()

