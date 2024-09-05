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
        self.subs.subscribe('dashboard')

        self.baseurl = "http://gps.maxux.net"
        self.backlogger = redis.Redis()

        self.states = {
            "transmitter": False,
            "session": None,
        }

        self.slave = dashboard.DashboardSlave("tracker")

    def session(self):
        response = requests.get(f"{self.baseurl}/api/push/session", headers=self.headers)
        status = response.json()

        return (status["status"] == "success")

    def backlog(self, message):
        self.backlogger.publish("tracker-backlog", message)

    def process(self, message):
        if not self.states["transmitter"]:
            return None

        if message['type'] != "message":
            return None

        entry = json.loads(message["data"].decode('utf-8'))
        if entry['id'] != "location":
            return None

        payload = entry['payload']
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

        # FIXME: only publish on changes
        self.slave.set(self.states)
        self.slave.publish()

        return True

    def monitor(self):
        while True:
            message = self.subs.get_message(ignore_subscribe_messages=True, timeout=1.0)
            # print(message)

            if message:
                self.process(message)

if __name__ == "__main__":
    tracker = MagibuxTracker()

    if len(sys.argv) > 1:
        print("CREATING NEW SESSION")
        tracker.session()

    tracker.states["transmitter"] = True
    tracker.monitor()
