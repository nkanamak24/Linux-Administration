from flask import Flask
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    conn = mysql.connector.connect(
        host="localhost",
        user="esimerkkikäyttäjä",
        password="1234",
        database="esimerkkidb"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
  
    utc_time = result[0]
    suomi_time = utc_time + timedelta(hours=2)
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
                font-size: 18px;
            }}
            button {{
                            background-color: #1E90FF;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 18px;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #4682B4;
                }}
        </style>
    </head>
    <body>
        <h1>Linux Administration, Tervetuloa ensimmäiselle sivulleni</h1>
        <p>Kellonaika tietokannasta (Suomen aika): {muotoiltu_aika}</p>
        <h3>Siirry Data-analyysiin</h3>
        <button onclick="siirryDataAnalyysiin()">Klikkaa tästä!</button>
        <script>
            function siirryDataAnalyysiin() {{
                window.location.href = 'http://195.148.22.146/data-analysis';
            }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)


