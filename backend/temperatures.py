import serial
import dashboard
import time
import json
import redis
import sys
import traceback
from tools.colors import color
from tools.readserial import ReadLine

class MagibuxTemperatures:
    def __init__(self, port):
        self.dashboard = dashboard.DashboardSlave("temperature")
        self.dashboard.print(f"[+] initializing, serial port: {port}")

        self.board = serial.Serial(port, 9600)
        self.reader = ReadLine(self.board)

        self.tempinfo = {}

    def loop(self):
        try:
            line = self.reader.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        self.dashboard.print(f"[<] {color.blue}{data}{color.reset}")

        items = data.split(": ")
        # print(items)

        if items[0] == "sensors":
            if items[1] == "end of batch":
                self.dashboard.commit()

        if items[0] == "temperature":
            id = items[1]
            value = round(float(items[2]), 1)

            previous = self.dashboard.get(id)
            if previous and previous["value"] == value:
                # still up-to-date
                return

            self.dashboard.print(f"[+] updating: {id}")
            self.dashboard.set(id, {"value": value, "changed": int(time.time())})

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
    port = "/dev/ttyCH9344USB2"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    sensors = MagibuxTemperatures(port)
    sensors.monitor()
