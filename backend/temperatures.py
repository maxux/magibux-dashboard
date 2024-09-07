import serial
import dashboard
import time
import json
import redis
import sys
import traceback

class MagibuxTemperatures:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        # self.queue = redis.Redis()

        self.temperature = dashboard.DashboardSlave("temperature")
        self.tempinfo = {}

    def loop(self):
        try:
            line = self.board.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        print(data)

        items = data.split(": ")
        # print(items)

        if items[0] == "sensors":
            if items[1] == "end of batch":
                self.temperature.set(self.tempinfo)
                self.temperature.publish()

        if items[0] == "temperature":
            id = items[1]
            value = float(items[2])

            self.tempinfo[id] = {"value": value, "changed": int(time.time())}

            """ FIXME
            persistance = {
                "type": "temperature",
                "source": items[1],
                "value": float(items[2])
            }

            # self.queue.publish("persistance", json.dumps(persistance))
            """

    def monitor(self):
        while True:
            self.loop()

if __name__ == "__main__":
    port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_950353138353517052E1-if00"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    sensors = MagibuxTemperatures(port)
    sensors.monitor()
