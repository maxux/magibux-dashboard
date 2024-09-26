import redis
import sys
import requests
import json
import time
import os
import dashboard
import traceback
from datetime import datetime
from config import config

class MagibuxTrackerBacklog:
    def __init__(self):
        self.redis = redis.Redis()
        self.queue = "tracker-backlog"

        self.baseurl = "http://gps.maxux.net"
        self.password = config['tracker-auth']
        self.headers = {"X-GPS-Auth": self.password}
        self.deviceid = 5

        self.dashboard = dashboard.DashboardSlave("tracking")
        self.lastupdate = 0

        self.stats = {
            "received": 0,
            "sent": 0,
            "retry": 0,
            "failed": 0,
            "backlog": 0,
        }

        if recovery := self.redis.get("tracker-stats"):
            self.stats = json.loads(recovery)

    def status(self):
        print(self.stats)

        if self.lastupdate > time.time() - 1.5:
            return

        print("notifying")
        self.dashboard.set("stats", self.stats)
        self.dashboard.commit()

        # persist stats
        self.redis.set("tracker-stats", json.dumps(self.stats))

        self.lastupdate = time.time()


    def size(self):
        pending = self.redis.llen(self.queue)

        self.stats["backlog"] = pending
        self.status()

    def transmit(self, message):
        # FIXME: support bundle of message

        print("TRANSMIT", message)
        try:
            url = f"{self.baseurl}/api/push/datapoint?device={self.deviceid}"

            response = requests.post(url, headers=self.headers, data=message, timeout=1.0)
            print(response)

            if response.status_code == 200:
                return True

            return False

        except Exception :
            traceback.print_exc()
            return None

    def consume(self, queue):
        print("CONSUME", queue)
        message = self.redis.blpop(queue, 5.0)

        if not message:
            print("Nothing found, retrying")
            return False

        self.stats["received"] += 1
        self.status()

        encoded = message[1]

        transmitted = False
        while not transmitted:
            transmitted = self.transmit(encoded)
            if transmitted:
                self.stats["sent"] += 1
                self.stats["retry"] = 0

                return True

            if transmitted is False:
                self.stats["failed"] += 1
                return None

            if transmitted is None:
                self.stats["retry"] += 1
                continue

    def monitor(self):
        while True:
            message = self.consume(self.queue)
            self.size()


if __name__ == "__main__":
    backlogger = MagibuxTrackerBacklog()
    backlogger.monitor()
