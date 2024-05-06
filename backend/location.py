import serial
import tools.nmea0183
import dashboard
import redis
import json
import math

class MagibuxLocator:
    def __init__(self, port):
        self.gps = serial.Serial(port, 9600)
        self.parser = tools.nmea0183.GPSData()
        self.places = redis.Redis()

        self.gga = {}

        self.slave = dashboard.DashboardSlave("location")
        self.previous = None
        self.trip = 0

    def distance(self, lat1, lon1, lat2, lon2):
        # haversine // https://www.movable-type.co.uk/scripts/latlong.html
        R = 6371000

        x1 = lat1 * math.pi / 180
        x2 = lat2 * math.pi / 180
        dp = (lat2 - lat1) * math.pi / 180
        da = (lon2 - lon1) * math.pi / 180

        a = math.sin(dp / 2) * math.sin(dp / 2)
        a += math.cos(x1) * math.cos(x2) * math.sin(da / 2) * math.sin(da / 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return float("%.2f" % (R * c))

    def place(self, lat, lon):
        listbase = self.places.georadius("geonames.main.base", lon, lat, 5, "km", "withdist", "asc")
        basedata = self.places.hget("geonames.data", listbase[0][0])

        base = json.loads(basedata)

        cdata = self.places.hget("geonames.countries", base[1])
        cinfo = json.loads(cdata)

        admin1 = self.places.hget("geonames.admin1", f"{base[1]}.{base[2]}").decode("utf-8")
        admin2 = self.places.hget("geonames.admin2", f"{base[1]}.{base[2]}.{base[3]}").decode("utf-8")

        return [base[0], admin2, admin1, cinfo["name"]]

    def loop(self):
        line = self.gps.readline()
        data = line.decode('utf-8').strip()

        parsed = self.parser.parse(data)
        print(parsed)

        if parsed['type'] not in ['rmc', 'gga']:
            # only process GPRMC and GPGGA for now
            return

        if parsed['type'] == 'gga':
            self.gga = parsed
            return

        coord = parsed['coord']
        parsed['place'] = self.place(coord['lat'], coord['lng'])

        if not self.previous:
            self.previous = coord

        # compute distance from last location
        distance = self.distance(coord['lat'], coord['lng'], self.previous['lat'], self.previous['lng'])
        # FIXME: skip if not enough
        parsed['delta'] = distance

        self.trip += distance
        parsed['trip'] = self.trip

        # inject hdop from gga
        if 'hdop' in self.gga:
            parsed['hdop'] = self.gga['hdop']

        self.slave.set(parsed)
        self.slave.publish()

        self.previous = coord

    def monitor(self):
        while True:
            self.loop()

if __name__ == "__main__":
    locator = MagibuxLocator("/dev/ttyACM0")
    locator.monitor()
