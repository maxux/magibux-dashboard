import serial
import dashboard
import redis
import sys

# // 28-ff641e93a11cb3: poste de conduite
# // 28-ff641f43f47d96: voyageur arrière conduite
# // 28-ff641e93d759d6: extérieur
# // 28-ff641e93b9a587: rack
# // 28-ff641f43f86666: front pannel (number)

class MagibuxSensors:
    def __init__(self, port):
        self.board = serial.Serial(port, 9600)
        self.queue = redis.Redis()

        self.temperature = dashboard.DashboardSlave("temperature")
        self.pressure = dashboard.DashboardSlave("pressure")

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

        if items[0] == "analog":
            source = self.pressure.payload

            value = items[1].split(" ")
            key = "rgn"

            if key not in source:
                source[key] = 0

            previous = source[key]
            now = float(value[0])
            source[key] = now

            self.pressure.set(source, key)

            if previous >= now + 0.05 or previous <= now - 0.05:
                print("pushing new value")
                self.pressure.publish()

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
