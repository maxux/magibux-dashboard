import serial
import dashboard
import time
import json
import redis
import sys
import traceback
from tools.colors import color
from tools.readserial import ReadLine

class MagibuxPressures:
    def __init__(self, port):
        self.dashboard = dashboard.DashboardSlave("pressure")
        self.dashboard.print(f"[+] initializing, serial port: {port}")

        self.board = serial.Serial(port, 9600)
        self.reader = ReadLine(self.board)
        # self.queue = redis.Redis()

        self.sensors = 10

        self.pressinfo = {}
        self.empty = {"value": 0, "time": 0, "way": None}

        for id in range(self.sensors):
            channel = f"channel-{id}"
            backfrom = self.dashboard.get(channel)
            self.pressinfo[channel] = backfrom or self.empty.copy()

    def loop(self):
        try:
            line = self.reader.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        self.dashboard.print(f"[<] {color.blue}{data}{color.reset}")

        items = data.split(": ")

        if items[0] == "pressure":
            values = items[1].split(" ")

            if len(values) != (self.sensors + 1):
                self.dashboard.print("[-] not enough data found")
                return

            if values[self.sensors] != "bar":
                self.dashboard.print("[-] malformed or incomplete values line")
                return

            commit = False

            for id, value in enumerate(values):
                if value == "bar":
                    break

                channel = f"channel-{id}"
                pressure = float(value)

                entry = self.pressinfo[channel]
                entry['way'] = None

                if pressure < entry['value'] - 0.04 or pressure > entry['value'] + 0.04:
                    entry['time'] = int(time.time())
                    entry['way'] = "down" if pressure < entry['value'] else "up"
                    entry['value'] = pressure

                    self.dashboard.print(f"[+] channel {id}: setting new value")
                    self.dashboard.set(channel, entry)

            self.dashboard.commit()

            """ FIXME
                persistance = {
                    "type": "pressure",
                    "source": key,
                    "value": float(value[0])
                }

                # self.queue.publish("persistance", json.dumps(persistance))
            """

    def monitor(self):
        while True:
            self.loop()

if __name__ == "__main__":
    # port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_85735313233351512171-if00"
    port = "/dev/ttyCH9344USB1"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    sensors = MagibuxPressures(port)
    sensors.monitor()
