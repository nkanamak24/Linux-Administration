from flask import Flask
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    conn = mysql.connector.connect(
        host="localhost",
        user="esimerkkikäyttäjä",
        password="Tämä_on_hyvä_salasana2",
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
    <!DOCTYPE html>
    <html>
    <head>
       
<meta charset="UTF-8">
<title>Samaa vanhaa</title>
<style>
    body {{
        background-color: #FFFF00;
        font-family: Arial, sans-serif;
        color: black;
        padding: 20px;
    }}
    h1 {{
        color: #8A2BE2;
    }}
    p {{
        font-size: 18px
    }}
        </style>
    </head>
    <body>
        <h1>Linux Administration, Tervetuloa ensimmäiselle sivulleni</h1>
        <p>Kellonaika tietokannasta (Suomen aika): {muotoiltu_aika}</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
