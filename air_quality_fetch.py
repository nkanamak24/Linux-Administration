#!/usr/bin/env python3
import ssl
try:
    import tornado.netutil

    def _ssl_wrap_socket(sock, ssl_options, server_side=False, **kwargs):
        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER if server_side else ssl.PROTOCOL_TLS_CLIENT
        )

        if isinstance(ssl_options, dict):
            certfile = ssl_options.get("certfile")
            keyfile = ssl_options.get("keyfile")
            if certfile:
                context.load_cert_chain(certfile, keyfile=keyfile)

            cert_reqs = ssl_options.get("cert_reqs")
            if cert_reqs is not None:
                context.verify_mode = cert_reqs
                ca_certs = ssl_options.get("ca_certs")
            if ca_certs:
                context.load_verify_locations(cafile=ca_certs)

            ciphers = ssl_options.get("ciphers")
            if ciphers:
                try:
                    context.set_ciphers(ciphers)
                except Exception:
                    pass

        return context.wrap_socket(sock, server_side=server_side, **kwargs)

    tornado.netutil.ssl_wrap_socket = _ssl_wrap_socket
except Exception:
    pass

import requests
import mysql.connector

from mysql.connector import Error
from datetime import datetime
import sys
import traceback

def log(msg):
    print(f"[air_quality_fetch] {datetime.now().isoformat()} | {msg}")

def main():
    try:
        lat, lon = 62.7907, 22.8398

url = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
    f"?latitude={lat}&longitude={lon}"
    "&hourly=pm2_5,pm10,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,european_aqi"
    "&timezone=Europe/Helsinki"
)
 log(f"Fetching: {url}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        resp = r.json()

        latest_index = -1
        time = resp["hourly"]["time"][latest_index]
        aqi = resp["hourly"]["european_aqi"][latest_index]
        pm25 = resp["hourly"]["pm2_5"][latest_index]
        pm10 = resp["hourly"]["pm10"][latest_index]

        log(f"Parsed: time={time}, AQI={aqi}, PM2.5={pm25}, PM10={pm10}")

        conn = mysql.connector.connect(
            host="localhost",
            user="esimerkkikäyttäjä",
            password="Tämä_on_hyvä_salasana2",
            database="weather_db",
            autocommit=True
        )
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO air_quality (timestamp, aqi, pm25, pm10)
            VALUES (%s, %s, %s, %s)
        """, (time, aqi, pm25, pm10))
        cur.close()
        conn.close()

        log("INSERT OK")

    except requests.exceptions.RequestException as e:
        log(f"HTTP error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Error as e:
        log(f"MySQL error: {e}")
        traceback.print_exc()
        sys.exit(2)
    except Exception as e:
        log(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()

