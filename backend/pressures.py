import serial
import dashboard
import time
import json
import redis
import sys

class MagibuxPressures:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        # self.queue = redis.Redis()

        self.sensors = 10

        self.pressure = dashboard.DashboardSlave("pressure")
        self.pressraw = [] * self.sensors
        self.pressinfo = []

        for i in range(self.sensors):
            self.pressinfo.append({
                'value': 0,
                'time': 0,
                'way': None,
            })

        self.lastcommit = self.pressinfo

    def loop(self):
        line = self.board.readline()

        try:
            data = line.decode('utf-8').strip()

        except Exception as e:
            print(e)
            return

        print(data)

        items = data.split(": ")

        if items[0] == "pressure":
            values = items[1].split(" ")

            if len(values) != (self.sensors + 1):
                print("[-] not enough data found")
                return

            if values[self.sensors] != "bar":
                print("[-] malformed or incomplete values line")
                return

            commit = False

            for id, value in enumerate(values):
                if value == "bar":
                    break

                pressure = float(value)

                entry = self.pressinfo[id]
                entry['way'] = None

                if pressure < entry['value'] - 0.04 or pressure > entry['value'] + 0.04:
                    entry['time'] = int(time.time())
                    entry['way'] = "down" if pressure < entry['value'] else "up"
                    entry['value'] = pressure

                    commit = True

            if commit:
                print("[+] pushing new value updated")
                self.pressure.set(self.pressinfo)
                self.pressure.publish()

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
    port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_85735313233351512171-if00"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    sensors = MagibuxPressures(port)
    sensors.monitor()
