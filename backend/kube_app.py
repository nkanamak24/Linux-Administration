import os
import html
from datetime import datetime, timezone

import pymysql
from pymysql.cursors import DictCursor
from flask import (
    Flask, request, redirect, Response, render_template_string, jsonify
)
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    from zoneinfo import ZoneInfo
    HELSINKI_TZ = ZoneInfo("Europe/Helsinki")
except Exception:
    HELSINKI_TZ = None


# --------------------------
# Apu: aikavyöhyke ja formatointi
# --------------------------
def to_helsinki(dt_utc):
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    if HELSINKI_TZ:
        return dt_utc.astimezone(HELSINKI_TZ)
    return dt_utc


def fmt_local(dt_utc):
    local = to_helsinki(dt_utc)
    return local.strftime("%Y-%m-%d %H:%M:%S") if local else ""


# --------------------------
# Ympäristömuuttujat / DB
# --------------------------
BASE_PATH = os.getenv("BASE_PATH", "/kube")

DB_HOST = os.getenv("DB_HOST", "mysql-svc")  # oletus Service-nimi
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "esimerkkikayttaja")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")


# --------------------------
# Flask & ProxyFix
# --------------------------
app = Flask(__name__, static_folder="static", static_url_path=f"{BASE_PATH}/static")
# reverse proxy -tuki (x_prefix auttaa base-pathissa)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_port=1, x_prefix=1)


# --------------------------
# DB-yhteys ja skeema
# --------------------------
def get_conn():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
    )
    # Aikavyöhyke DB:lle (ei pakollinen)
    try:
        with conn.cursor() as c:
            try:
                c.execute("SET time_zone = 'Europe/Helsinki'")
            except Exception:
                c.execute("SET time_zone = '+02:00'")
    except Exception:
        pass
    return conn


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id INT AUTO_INCREMENT PRIMARY KEY,
              content TEXT NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# --------------------------
# Healthz (text/plain)
# --------------------------
@app.route(f"{BASE_PATH}/healthz")
@app.route("/healthz")
def healthz():
    try:
        conn = get_conn()
        conn.close()
    except Exception:
        pass
    return Response("ok\n", status=200, content_type="text/plain; charset=utf-8")


# --------------------------
# Etusivu (UI)
# --------------------------
@app.route(f"{BASE_PATH}", methods=["GET", "POST"])
@app.route(f"{BASE_PATH}/", methods=["GET", "POST"])
def index():
    db_ok = True
    rows = []
    conn = None

    try:
        conn = get_conn()
        ensure_schema(conn)

        if request.method == "POST":
            content = (request.form.get("content", "") or "").strip()
            if content:
                with conn.cursor() as cur:
                    now_utc = datetime.utcnow()
                    cur.execute(
                        "INSERT INTO messages (content, created_at) VALUES (%s, %s)",
                        (content, now_utc),
                    )
                return redirect(f"{BASE_PATH}/")

        # Listaus
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC")
            rows = cur.fetchall()

        for r in rows:
            dt = r.get("created_at")
            if isinstance(dt, str):
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = None
            r["created_at_local"] = fmt_local(dt)

    except Exception:
        db_ok = False
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    if db_ok and rows:
        items_html = "\n".join(
            f"&lt;li&gt;{html.escape(r['content'])} "
            f"({html.escape(r.get('created_at_local') or str(r.get('created_at')))})&lt;/li&gt;"
            for r in rows
        )
    elif db_ok and not rows:
        items_html = "&lt;li&gt;(Ei viestejä vielä)&lt;/li&gt;"
    else:
        items_html = "&lt;li&gt;(DB ei vielä käytettävissä)&lt;/li&gt;"

    html_tpl = f"""&lt;!doctype html&gt;
&lt;html lang="fi"&gt;
  &lt;head&gt;
    &lt;meta charset="utf-8"&gt;
    &lt;title&gt;Linux Administration Kube&lt;/title&gt;
    {BASE_PATH}/
    &lt;style&gt;
      body {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        max-width: 720px; margin: 2rem auto; padding: 0 1rem;
      }}
      form {{ display: flex; gap: .5rem; }}
      input[name="content"] {{ flex: 1; padding: .5rem; }}
      button {{ padding: .5rem 1rem; }}
      ul {{ margin-top: 1rem; }}
      .warn {{ color:#b00; }}
      .btnbar {{ margin-top: 1rem; display:flex; gap:.5rem; flex-wrap:wrap; }}
      pre#result {{
        background:#f7f7f7; border:1px solid #ddd; padding:.75rem;
        border-radius:.25rem; margin-top:.5rem; white-space: pre-wrap;
      }}
    &lt;/style&gt;
  &lt;/head&gt;
  &lt;body&gt;

    &lt;h1&gt;Linux Administration Kube&lt;/h1&gt;

    {"&lt;p class='warn'&gt;Huom: MariaDB/MySQL ei ole vielä käytettävissä.&lt;/p&gt;" if not db_ok else ""}

    &lt;form method="post" action=""&gt;
      &lt;input name="content" type="text" placeholder="Kirjoita viesti"&gt;
      &lt;button type="submit"&gt;Tallenna&lt;/button&gt;
    &lt;/form&gt;

    &lt;div class="btnbar"&gt;
      &lt;button id="btn-health"&gt;Check Backend Health&lt;/button&gt;
      &lt;button id="btn-init"&gt;Initialize Database&lt;/button&gt;
      &lt;button id="btn-get"&gt;Get Messages&lt;/button&gt;
    &lt;/div&gt;

    &lt;pre id="result"&gt;&lt;/pre&gt;

    &lt;ul&gt;
      {items_html}
    &lt;/ul&gt;

    &lt;script&gt;
      async function callApi(path, options) {{
        const resp = await fetch(path, Object.assign({{
          headers: {{ "Accept":"application/json", "Content-Type":"application/json" }}
        }}, options || {{}}));
        const ct = resp.headers.get('content-type') || '';
        if (!resp.ok) {{
          const text = await resp.text();
          throw new Error(`HTTP ${resp.status} ${resp.statusText} — ${text}`);
        }}
        if (ct.includes('application/json')) {{
          return await resp.json();
        }} else {{
          const text = await resp.text();
          try {{ return JSON.parse(text); }} catch {{ return {{ raw: text }}; }}
        }}
      }}

      const resultEl = document.getElementById('result');
      function showResult(data) {{ resultEl.textContent = JSON.stringify(data, null, 2); }}
      function showError(err)  {{ resultEl.textContent = 'Error: ' + String(err); }}

      // Suhteelliset polut -> kun ollaan /kube/ sivulla, nämä osuvat /kube/api/...
      document.getElementById('btn-health').onclick = async () => {{
        try {{ showResult(await callApi('api/health')); }} catch(e){{ showError(e); }}
      }};
      document.getElementById('btn-init').onclick = async () => {{
        try {{ showResult(await callApi('api/init-db', {{ method: 'POST' }})); }} catch(e){{ showError(e); }}
      }};
      document.getElementById('btn-get').onclick = async () => {{
        try {{ showResult(await callApi('api/messages')); }} catch(e){{ showError(e); }}
      }};
    &lt;/script&gt;

  &lt;/body&gt;
&lt;/html&gt;"""

    return render_template_string(html_tpl), 200


@app.route("/", methods=["GET"])
def root_redirect():
    return redirect(f"{BASE_PATH}/")


# --------------------------
# JSON API -reitit
# --------------------------

# Terveyspolku kahdella reitillä: ilman BASE_PATH (probe) ja BASE_PATH:in kanssa (frontend)
@app.route("/api/health", methods=["GET"])
@app.route(f"{BASE_PATH}/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "healthy"}), 200


# Init DB: POST (ei GET) – jotta frontendin POST ei tuota 405:ttä
@app.route("/api/init-db", methods=["POST"])
@app.route(f"{BASE_PATH}/api/init-db", methods=["POST"])
def api_init_db():
    conn = None
    try:
        conn = get_conn()
        ensure_schema(conn)
        return jsonify({"status": "initialized", "tables": ["messages"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 503
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# Messages: GET (listaa) ja POST (tallenna) samassa reitissä
@app.route("/api/messages", methods=["GET", "POST"])
@app.route(f"{BASE_PATH}/api/messages", methods=["GET", "POST"])
def api_messages():
    conn = None
    try:
        conn = get_conn()
        ensure_schema(conn)

        if request.method == "GET":
            with conn.cursor() as cur:
                cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC")
                rows = cur.fetchall()

            for r in rows:
                dt = r.get("created_at")
                if isinstance(dt, str):
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = None
                r["created_at_local"] = fmt_local(dt)

            return jsonify(rows), 200

        # POST: tallenna
        data = request.get_json(silent=True) or {}
        content = (data.get("text") or "").strip()
        if not content:
            return jsonify({"error": "text required"}), 400

        with conn.cursor() as cur:
            now_utc = datetime.utcnow()
            cur.execute(
                "INSERT INTO messages (content, created_at) VALUES (%s, %s)",
                (content, now_utc),
            )
            new_id = cur.lastrowid

        return jsonify({"saved": True, "message": {"id": int(new_id), "text": content}}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 503
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# Yhteensopivuus: vanha polku käyttää samaa POST-logiikkaa kuin /api/messages
@app.route(f"{BASE_PATH}/api/save-message", methods=["POST"])
def api_save_message():
    return api_messages()


@app.route("/api/db-status", methods=["GET"])
@app.route(f"{BASE_PATH}/api/db-status", methods=["GET"])
def api_db_status():
    try:
        conn = get_conn()
        conn.close()
        return jsonify({"db_ok": True, "host": DB_HOST}), 200
    except Exception as e:
        return jsonify({"db_ok": False, "error": str(e)}), 503


# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    # pysytään 8080:ssa, koska backend.yaml odottaa tätä
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
