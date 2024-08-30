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

        if "locationpwd" not in os.environ:
            raise RuntimeError("No tracking password set (via environment variable)")

        self.password = os.environ["locationpwd"]
        self.headers = {"X-GPS-Auth": self.password}

        self.transmitter = False
        self.backlog = []
        self.stats = {
            "sent": 0,
            "ack": 0,
            "timeout": 0,
            "skip": 0,
        }

        self.slave = dashboard.DashboardSlave("tracker")

    def session(self):
        response = requests.get(f"{self.baseurl}/api/push/session", headers=self.headers)
        status = response.json()

        return (status["status"] == "success")

    def monitor(self):
        while True:
            message = self.subs.get_message(ignore_subscribe_messages=True, timeout=1.0)
            # print(message)

            if not self.transmitter:
                continue

            if message is None:
                continue

            if message['type'] != "message":
                continue

            entry = json.loads(message["data"].decode('utf-8'))
            if entry['id'] != "location":
                continue

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
                "alt": 0,
                "ts": payload['timestamp'],
            }

            encoded = json.dumps(frame)
            print(encoded)

            try:
                response = requests.post(f"{self.baseurl}/api/push/datapoint", headers=self.headers, data=encoded, timeout=1.0)
                if response.status_code == 200:
                    self.stats['sent'] += 1

                print(response)

            except requests.exceptions.Timeout:
                print("REQUEST TIMED OUT, IMPLEMENT BACKLOG")
                self.stats['timeout'] += 1

            print(self.stats)

            self.slave.set(self.stats)
            self.slave.publish()

if __name__ == "__main__":
    tracker = MagibuxTracker()

    if len(sys.argv) > 1:
        print("CREATING NEW SESSION")
        tracker.session()

    tracker.transmitter = True
    tracker.monitor()
