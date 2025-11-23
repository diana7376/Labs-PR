from flask import Flask, request, jsonify
import os

app = Flask(__name__)
store = {}  # Simple in-memory key-value

# Endpoint for reading values
@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    value = store.get(key)
    return jsonify({'key': key, 'value': value})

# Endpoint for replication (called by leader)
@app.route('/replicate/<key>', methods=['POST'])
def replicate(key):
    value = request.json['value']
    store[key] = value
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))  # Default 8001; overwritten by docker-compose env
    app.run(host="0.0.0.0", port=port, threaded=True)
