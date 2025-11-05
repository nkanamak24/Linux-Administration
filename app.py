from flask import Flask
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    conn = mysql.connector.connect(
        host="localhost",
        user="esimerkkikäyttäjä",
        password="salasana",
        database="esimerkkidb"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    # Muunna UTC -> Suomen aika (talviaika oletuksena)
    utc_time = result[0]
    suomi_time = utc_time + timedelta(hours=2)

    # Muotoile päivämäärä suomalaiseen muotoon: pp.kk.vvvv klo hh:mm:ss
    muotoiltu_aika = suomi_time.strftime("%d.%m.%Y klo %H:%M:%S")

    return f"""
    <html>
        <head><title>Uutta ja ihmeellistä</title></head>
        <body>
            <h1>Linux Administration, Tervetuloa toiselle sivulleni</h1>
            <p>Kellonaika tietokannasta (Suomen aika): {muotoiltu_aika}</p>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
