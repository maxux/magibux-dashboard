import serial
import dashboard
import json
import time
import redis
import sys
import traceback

class MagibuxRelay:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        self.queue = redis.Redis()

        self.control = redis.Redis()
        self.ctrlsub = self.control.pubsub()
        self.ctrlsub.subscribe(['relaying'])

        self.slave = dashboard.DashboardSlave("relay")
        self.channels = 8
        self.state = [None] * self.channels
        self.uptime = [None] * self.channels

    def serial_loop(self):
        try:
            line = self.board.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        print(data)

        items = data.split(": ")
        # print(items)

        if items[0].startswith("state"):
            state = items[1].split(" ")

            merged = [(None, None)] * self.channels
            changed = False

            for idx, value in enumerate(state):
                if self.state[idx] != int(value):
                    self.state[idx] = int(value)
                    self.uptime[idx] = int(time.time())

                    changed = True

                # create a merged view of state and uptime
                merged[idx] = (int(value), self.uptime[idx])

            if changed:
                print(f"[+] new state: {merged}")

                self.slave.set(merged)
                self.slave.publish()

    def control_loop(self):
        message = self.ctrlsub.get_message()
        if message is None:
            return

        if message['type'] != 'message':
            return

        try:
            payload = json.loads(message['data'])

        except Exception as e:
            print(e)
            return

        channel = payload['id']
        print(payload)

        if payload["action"] == "enable":
            print(f"[+] enabling channel: {channel}")
            self.board.write(f"E{channel}\n".encode('utf-8'))

        if payload["action"] == "disable":
            print(f"[+] disabling channel: {channel}")
            self.board.write(f"D{channel}\n".encode('utf-8'))

    def monitor(self):
        while True:
            self.control_loop()
            self.serial_loop()

if __name__ == "__main__":
    port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_142353030363512160C1-if00"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    relay = MagibuxRelay(port)
    relay.monitor()
