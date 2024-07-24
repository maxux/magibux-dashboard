import serial
import dashboard
import json
import redis
import sys

class MagibuxRelay:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        self.queue = redis.Redis()

        self.control = redis.Redis()
        self.ctrlsub = self.control.pubsub()
        self.ctrlsub.subscribe(['relaying'])

        self.relay = dashboard.DashboardSlave("relay")

    def serial_loop(self):
        line = self.board.readline()
        data = line.decode('utf-8').strip()

        print(data)

        items = data.split(": ")
        # print(items)

        if items[0].startswith("state"):
            print(items)

    def control_loop(self):
        message = self.ctrlsub.get_message()
        if message is None:
            return

        if message['type'] != 'message':
            return

        payload = json.loads(message['data'])
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
    port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_8533231303635131CC45-if00"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    relay = MagibuxRelay(port)
    relay.monitor()
