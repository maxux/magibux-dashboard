import redis
import sys
import requests
import json
import time
import os
import dashboard
from datetime import datetime

class MagibuxTracker:
    def __init__(self):
        self.redis = redis.Redis()
        self.subs = self.redis.pubsub()
        self.subs.subscribe("dashboard", "tracker-update")

        if "locationpwd" not in os.environ:
            raise RuntimeError("No tracking password set (via environment variable)")

        self.baseurl = "http://gps.maxux.net"
        self.password = os.environ["locationpwd"]
        self.headers = {"X-GPS-Auth": self.password}

        self.backlogger = redis.Redis()

        self.states = {
            "transmitter": False,
            "session": None,
        }

        self.slave = dashboard.DashboardSlave("tracker")

    def session_create(self):
        response = requests.get(f"{self.baseurl}/api/push/session", headers=self.headers)
        status = response.json()

        return (status["status"] == "success")

    def backlog(self, message):
        self.backlogger.publish("tracker-backlog", message)

    def process_update(self, message):
        print("Tracker update requested")

        if message["request"] == "transmitter-enable":
            print("[+] transmission enabled")
            self.states["transmitter"] = True

        if message["request"] == "transmitter-disable":
            print("[+] transmission disabled")
            self.states["transmitter"] = False

        if message["request"] == "new-session":
            print("[+] new session requested, creating")
            self.session_create()

        # sending updated state
        self.slave.set(self.states)
        self.slave.publish()

    def process_dashboard(self, message):
        # ignore everything except 'location' update
        if message["id"] != "location":
            return None

        if not self.states["transmitter"]:
            print("Location received but transmitter disabled")
            return None

        payload = message['payload']
        print(payload)

        now = datetime.now()

        frame = {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "class": "gps",
            "acc": 1,
            "lat": payload['coord']['lat'],
            "lng": payload['coord']['lng'],
            "speed": payload['speed'],
            "alt": payload['altitude'],
            "ts": payload['timestamp'],
        }

        encoded = json.dumps(frame)
        print(encoded)

        print("-- BACKLOGGING --")
        self.backlogger.rpush("tracker-backlog", encoded)

        return True

    def monitor(self):
        # sending initial state
        self.slave.set(self.states)
        self.slave.publish()

        while True:
            message = self.subs.get_message(ignore_subscribe_messages=True, timeout=1.0)
            # print(message)

            if not message:
                continue

            if message["type"] != "message":
                continue

            if message["channel"].decode("utf-8") == "dashboard":
                content = json.loads(message["data"].decode('utf-8'))
                self.process_dashboard(content)

            if message["channel"].decode("utf-8") == "tracker-update":
                content = json.loads(message["data"].decode('utf-8'))
                self.process_update(content)

if __name__ == "__main__":
    tracker = MagibuxTracker()

    # FIXME: restore last state
    tracker.states["transmitter"] = False

    tracker.monitor()
