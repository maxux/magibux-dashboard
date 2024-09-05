from flask import Flask, request, jsonify
import json
import redis

r = redis.Redis()
app = Flask(__name__)

@app.route("/control/poweron/<id>")
def relay_on(id):
    payload = {"action": "enable", "id": id}
    r.publish("relaying", json.dumps(payload))

    return jsonify({"status": "success"})

@app.route("/control/poweroff/<id>")
def relay_off(id):
    payload = {"action": "disable", "id": id}
    r.publish("relaying", json.dumps(payload))

    return jsonify({"status": "success"})

@app.route("/control/transmitter/enable")
def transmitter_enable():
    payload = {"request": "transmitter-enable"}
    r.publish("tracker-update", json.dumps(payload))

    return jsonify({"status": "success"})

@app.route("/control/transmitter/disable")
def transmitter_disable():
    payload = {"request": "transmitter-disable"}
    r.publish("tracker-update", json.dumps(payload))

    return jsonify({"status": "success"})

@app.route("/control/tracker/new-session")
def tracker_new_session():
    payload = {"request": "new-session"}
    r.publish("tracker-update", json.dumps(payload))

    return jsonify({"status": "success"})

print("[+] listening")
app.run(host="0.0.0.0", port=8099, debug=True, threaded=True)

