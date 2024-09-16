import serial
import time
import tools.nmea0183
import dashboard
import redis
import json
import math
import sys
import traceback

class MagibuxLocator:
    def __init__(self, port):
        self.gps = serial.Serial(port, 9600)
        self.parser = tools.nmea0183.GPSData()
        self.places = redis.Redis()

        self.frame = self.reset()

        self.dashboard = dashboard.DashboardSlave("location")
        self.previous = None
        self.trip = 0

        self.odometer = self.places.get("odometer")
        if self.odometer:
            self.odometer = float(self.odometer)

    def reset(self):
        frame = {
            "gga": None,
            "vtg": None,
            "rmc": None
        }

        return frame

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
        try:
            line = self.gps.readline()
            data = line.decode('utf-8').strip()

        except Exception:
            traceback.print_exc()
            return

        parsed = self.parser.parse(data)
        print(parsed)

        if parsed['type'] not in ['rmc', 'gga', 'vtg']:
            # only process GPRMC, GPGGA and GPVTG for now
            return

        self.frame[parsed['type']] = parsed

        if self.frame['rmc'] and self.frame['gga'] and self.frame['vtg']:
            return self.commit()

    def commit(self):
        print("--- COMMIT ---")
        response = {}

        coord = self.frame['rmc']['coord']

        if not coord['lat'] or not coord['lng']:
            return

        response['coord'] = coord
        response['speed'] = self.frame['vtg']['kph']
        response['place'] = None
        response['timestamp'] = self.frame['rmc']['timestamp']
        response['altitude'] = self.frame['gga']['altitude']

        try:
            response['place'] = self.place(coord['lat'], coord['lng'])

        except Exception:
            traceback.print_exc()

        if not self.previous:
            self.previous = coord

        # compute distance from last location
        distance = self.distance(coord['lat'], coord['lng'], self.previous['lat'], self.previous['lng'])

        response['delta'] = distance

        if response['speed'] >= 2:
            self.trip += distance
            self.odometer += distance

            self.places.set("odometer", self.odometer)

        response['trip'] = self.trip
        response['odometer'] = self.odometer

        # inject hdop from gga
        if 'hdop' in self.frame['gga']:
            response['hdop'] = self.frame['gga']['hdop']

        self.dashboard.set("live", response)
        self.dashboard.commit()

        # FIXME: add persistance

        self.previous = coord
        self.frame = self.reset()

    def monitor(self):
        while True:
            try:
                self.loop()

            except Exception:
                traceback.print_exc()
                return False


if __name__ == "__main__":
    port = "/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00"

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"[+] opening serial port: {port}")

    while True:
        locator = MagibuxLocator(port)
        locator.monitor()
