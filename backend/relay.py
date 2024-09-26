import serial
import dashboard
import json
import time
import redis
import sys
import traceback
from tools.colors import color

class MagibuxRelay:
    def __init__(self, port):
        self.dashboard = dashboard.DashboardSlave("relay")
        self.dashboard.print(f"[+] initializing, serial port: {port}")

        self.board = serial.Serial(port, 9600, timeout=0.2)
        self.queue = redis.Redis()

        self.control = redis.Redis()
        self.ctrlsub = self.control.pubsub()
        self.ctrlsub.subscribe(['relaying'])

        self.channels = 8
        self.state = {}
        self.empty = {"state": None, "changed": 0}

        for id in range(self.channels):
            channel = f"channel-{id}"
            backfrom = self.dashboard.get(channel)
            self.state[channel] = backfrom or self.empty.copy()

    def serial_loop(self):
        try:
            line = self.board.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        if len(data) == 0:
            return

        self.dashboard.print(f"[<] {color.blue}{data}{color.reset}")

        items = data.split(": ")
        # print(items)

        if items[0] == "state":
            state = items[1].split(" ")
            if len(state) != self.channels:
                # FIXME: add sentinel
                self.dashboard.print("[-] wrong amount of channels read")
                return

            for idx, value in enumerate(state):
                channel = f"channel-{idx}"

                if self.state[channel]["state"] != int(value):
                    self.state[channel]["state"] = int(value)
                    self.state[channel]["changed"] = int(time.time())
                    self.dashboard.set(channel, self.state[channel])

            self.dashboard.commit()

    def control_loop(self):
        message = self.ctrlsub.get_message()
        if message is None:
            return

        if message['type'] != 'message':
            return

        try:
            payload = json.loads(message['data'])

        except Exception:
            traceback.print_exc()
            return

        channel = payload['id']
        print(payload)

        if payload["action"] == "enable":
            self.dashboard.print(f"[+] enabling channel: {channel}")
            self.board.write(f"E{channel}\n".encode('utf-8'))

        if payload["action"] == "disable":
            self.dashboard.print(f"[+] disabling channel: {channel}")
            self.board.write(f"D{channel}\n".encode('utf-8'))

    def monitor(self):
        while True:
            # FIXME: remote action is checked only when serial have new data
            self.control_loop()
            self.serial_loop()

if __name__ == "__main__":
    port = "/dev/ttyCH9344USB0"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    relay = MagibuxRelay(port)
    relay.monitor()
