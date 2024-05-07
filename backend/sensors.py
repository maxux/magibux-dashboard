import serial
import dashboard
import json
import redis
import sys

class MagibuxSensors:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        self.queue = redis.Redis()

        self.temperature = dashboard.DashboardSlave("temperature")
        self.pressure = dashboard.DashboardSlave("pressure")

        self.channels = {
            "press1": "RGN",
            "press0": "RGE"
        }

    def loop(self):
        line = self.board.readline()
        data = line.decode('utf-8').strip()

        print(data)

        items = data.split(": ")
        # print(items)

        if items[0] == "temperature":
            source = self.temperature.payload
            source[items[1]] = float(items[2])

            self.temperature.set(source, items[1])
            self.temperature.publish()

            persistance = {
                "type": "temperature",
                "source": items[1],
                "value": float(items[2])
            }

            self.queue.publish("persistance", json.dumps(persistance))

        if items[0].startswith("press"):
            source = self.pressure.payload

            value = items[1].split(" ")
            key = self.channels[items[0]]

            if key not in source:
                source[key] = 0

            previous = source[key]
            now = float(value[0])
            source[key] = now

            if previous >= now + 0.05 or previous <= now - 0.05:
                self.pressure.set(source, key)
                self.pressure.publish()

                persistance = {
                    "type": "pressure",
                    "source": key,
                    "value": float(value[0])
                }

                self.queue.publish("persistance", json.dumps(persistance))

    def monitor(self):
        while True:
            self.loop()

if __name__ == "__main__":
    port = "/dev/ttyACM1"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    sensors = MagibuxSensors(port)
    sensors.monitor()
