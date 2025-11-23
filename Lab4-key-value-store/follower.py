from flask import Flask, request, jsonify
import threading
import os

app = Flask(__name__)
store = {}  # simple in-memory key-value

# ---------- Basic Key-Value Store Logic ----------
@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    value = store.get(key)
    return jsonify({'key': key, 'value': value})

# ---------- Replication Logic ----------
@app.route('/replicate/<key>', methods=['POST'])
def replicate(key):
    value = request.json['value']
    store[key] = value
    return jsonify({'status': 'ok'})

