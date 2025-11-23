from flask import Flask, request, jsonify
import threading
import os
import requests
import time
import random

# ---------- Basic Key-Value Store Logic ----------
app = Flask(__name__)
store = {}  # simple in-memory key-value

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    value = store.get(key)
    return jsonify({'key': key, 'value': value})

# ---------- Replication and Quorum Logic ----------

FOLLOWERS = os.environ.get('FOLLOWERS').split(',')
WRITE_QUORUM = int(os.environ.get('WRITE_QUORUM', '3'))
MIN_DELAY = float(os.environ.get('MIN_DELAY', '0.0001'))
MAX_DELAY = float(os.environ.get('MAX_DELAY', '0.001'))

@app.route('/put/<key>', methods=['POST'])
def put_value(key):
    value = request.json['value']
    store[key] = value  # write locally

    # Replication
    results = []
    def replicate(follower_url):
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)
        try:
            resp = requests.post(
                f"http://{follower_url}/replicate/{key}",
                json={"value": value}
            )
            if resp.status_code == 200:
                results.append(True)
        except Exception:
            results.append(False)

    threads = []
    for follower in FOLLOWERS:
        t = threading.Thread(target=replicate, args=(follower,))
        t.start()
        threads.append(t)

    # Wait for quorum
    start = time.time()
    while True:
        if results.count(True) >= WRITE_QUORUM:
            latency = time.time() - start
            return jsonify({'status': 'ok', 'latency': latency}), 200
        if len(results) == len(FOLLOWERS):
            break
        time.sleep(0.001)

    latency = time.time() - start
    return jsonify({'status': 'fail', 'latency': latency}), 500
