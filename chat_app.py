from flask import Flask, jsonify, render_template, request
import mysql.connector
import os
from mysql.connector import Error
import paho.mqtt.publish as publish
from datetime import datetime
import zoneinfo

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "mqtt_chat"),
    "autocommit": True,
}

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "chat/messages")

FI_TZ = zoneinfo.ZoneInfo("Europe/Helsinki")
UTC_TZ = zoneinfo.ZoneInfo("UTC")


@app.route('/chat')
@app.route('/chat/')
def chat():
    return render_template('index.html')  # templates/index.html


@app.route('/api/messages')
def get_messages():
    """Palauttaa viimeiset 10 viestiä tietokannasta"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, message, created_at
            FROM messages
            ORDER BY created_at DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        result = []
        for r in rows:
            dt = r["created_at"]
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC_TZ)
                dt_fi = dt.astimezone(FI_TZ)
                dt_str = dt_fi.strftime("%Y-%m-%d %H:%M:%S %Z")
                 else:
                dt_str = ""

            result.append({
                "id": r["id"],
                "message": r["message"],
                "created_at": dt_str
            })
        return jsonify(result)
    except Error as e:
        return jsonify({"error": f"DB error: {str(e)}"}), 500


@app.route('/send', methods=['POST'])
def send_message():
    """Lähettää viestin MQTT:lle (ei tallenna tietokantaan)"""
    message = (request.form.get('message') or '').strip()
    client_id = request.headers.get('X-Client-Id', '')

    if not message:
        return "Virhe: viesti vaaditaan", 400

    payload = {
        "message": message,
        "clientId": client_id
    }
    try:
        publish.single(MQTT_TOPIC, payload=str(payload).replace("'", '"'),
                       hostname=MQTT_BROKER, port=MQTT_PORT)
   except Exception as e:
        return f"MQTT error: {str(e)}", 500

    return "Viesti lähetetty!", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)

                   
