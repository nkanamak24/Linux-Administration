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
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Uutta ja ihmeellistä</title>
        <style>
            body {{
                background-color: #8A2BE2;
                font-family: Arial, sans-serif;
                color: white;
                padding: 20px;
            }}
            h1 {{
                color: #FFFF00;
            }}
            p {{
                font-size: 18px;
            }}
            button {{
                padding: 10px 20px;
                font-size: 16px;
                margin-top: 10px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>Linux Administration, Tervetuloa toiselle sivulleni</h1>
        <p>Kellonaika tietokannasta (Suomen aika): {muotoiltu_aika}</p>
	<h2>Tämä sivu toimii Flask-sovelluksena. Flask-sovellus on asetettu toimimaan Nginx-reverse proxyn takana.</h2>
        <h3>Noppapeli: Yritä saada kutonen!</h3>
        <button onclick="heitäNoppa()">Heitä noppaa</button>
        <p id="noppaTulos"></p>

        <script>
            function heitäNoppa() {{
                const tulos = Math.floor(Math.random() * 6) + 1;
                const viesti = tulos === 6
                    ? "Onneksi olkoon! Sait kutosen, sinä voitit! "
                    : "Sait " + tulos + "      Yritä uudelleen!";
                document.getElementById("noppaTulos").textContent = viesti;
            }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
