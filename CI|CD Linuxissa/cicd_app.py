
from flask import Flask, jsonify, render_template
import os
import time

try:
    import redis
except ImportError:
    redis = None

app = Flask(__name__, template_folder='templates')

def get_redis():
    if not redis:
        return None
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    try:
        r = redis.Redis(host=host, port=port, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

@app.route('/')
def index():

    counter = 0
    r = get_redis()
    if r:
        try:
            counter = r.incr("visits")
        except Exception:
            counter = -1
    return render_template('index.html', counter=counter)

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/health/live')
def live():
    return jsonify({'status': 'alive'}), 200

@app.route('/health/ready')
def ready():
    r = get_redis()
    if r:
        try:
            r.ping()
            return jsonify({'status': 'ready', 'redis': 'connected'}), 200
        except Exception as e:
            return jsonify({'status': 'not ready', 'error': str(e)}), 503
    else:
        return jsonify({'status': 'not ready', 'error': 'redis unavailable'}), 503

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
