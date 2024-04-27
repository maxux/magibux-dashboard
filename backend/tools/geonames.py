import redis
import requests
import zipfile
import tempfile
import shutil
import json
import io

class GeoNamesRedis():
    def __init__(self):
        # http://download.geonames.org/export/dump/countryInfo.txt
        # http://download.geonames.org/export/dump/BE.zip
        # http://download.geonames.org/export/dump/admin1CodesASCII.txt
        # http://download.geonames.org/export/dump/admin2Codes.txt

        self.redis = redis.Redis()

        # geonames base url
        self.baseurl = "http://download.geonames.org/export/dump"

        # workding temporary directory
        self.workdir = tempfile.mkdtemp(prefix="geonames-")
        print(f"[+] working directory: {self.workdir}")

    def __del__(self):
        print(f"[+] cleaning up workdir: {self.workdir}")
        shutil.rmtree(self.workdir)

    def countries_from_continent(self, continent, excludes=[]):
        print("[+] downloading country info file")
        keep = []

        contents = requests.get(f"{self.baseurl}/countryInfo.txt")
        countries = contents.text.strip().split("\n")

        for country in countries:
            # ignore comments
            if country.startswith("#"):
                continue

            fields = country.split("\t")
            if fields[8] == continent and fields[0] not in excludes:
                keep.append(fields[0])

            # keep country name in database
            info = {
                "name": fields[4],
                "capital": fields[5]
            }

            self.redis.hset("geonames.countries", fields[0], json.dumps(info))

        return keep

    def countries_download(self, countries):
        print(f"[+] downloading and extracting {len(countries)} countries")

        for file in countries:
            print(f"[+] downloading and extracting: {file}.zip")

            download = requests.get(f"{self.baseurl}/{file}.zip")
            bio = io.BytesIO(download.content)

            with zipfile.ZipFile(bio, "r") as zf:
                zf.extractall(self.workdir)

    def database_cleanup(self):
        print("[+] cleaning up redis database")

        self.redis.delete("geonames.main.base")
        self.redis.delete("geonames.admin1")
        self.redis.delete("geonames.admin2")
        self.redis.delete("geonames.data")
        self.redis.delete("geonames.countries")
        # self.redis.delete("geonames.main.detailed")

    def basecodes(self):
        print("[+] downloading and inserting: admin1 codes")
        adm1 = requests.get(f"{self.baseurl}/admin1CodesASCII.txt")

        for line in adm1.text.strip().split("\n"):
            fields = line.split("\t")
            self.redis.hset("geonames.admin1", fields[0], fields[1])

        print("[+] downloading and inserting: admin2 codes")
        adm2 = requests.get(f"{self.baseurl}/admin2Codes.txt")
        for line in adm2.text.strip().split("\n"):
            fields = line.split("\t")
            self.redis.hset("geonames.admin2", fields[0], fields[1])

    def country_process(self, country):
        print(f"[+] processing country: {country}")
        f = open(f"{self.workdir}/{country}.txt", "r")

        for line in f.readlines():
            fields = line.split("\t")

            # A: country, state, region, ...
            if fields[6] == "A":
                self.redis.geoadd("geonames.main.base", (float(fields[5]), float(fields[4]), fields[0]))

            # P: city, village, ...
            # if fields[6] == "P":
            #    self.redis.geoadd("geonames.main.detailed", (float(fields[5]), float(fields[4]), fields[0]))

            # H: stream, lake, ...
            # L: parks,area, ...
            # R: road, railroad
            # S: spot, building, farm
            # T: mountain,hill,rock, ...
            # U: undersea
            # V: forest,heath, ...

            # if fields[6] not in ["A", "P"]:
            if fields[6] not in ["A"]:
                continue

            info = [fields[1], country, fields[10], fields[11]]
            self.redis.hset("geonames.data", fields[0], json.dumps(info))

    def resolv(self, lat, lon):
        listbase = self.redis.georadius("geonames.main.base", lon, lat, 5, "km", "withdist", "asc")
        # listdetail = self.redis.georadius("geonames.main.detailed", lon, lat, 5, "km", "withdist", "asc")

        basedata = self.redis.hget("geonames.data", listbase[0][0])
        # detaildata = self.redis.hget("geonames.data", listdetail[0][0])

        base = json.loads(basedata)
        # detail = json.loads(detaildata)

        cdata = self.redis.hget("geonames.countries", base[1])
        cinfo = json.loads(cdata)

        admin1 = self.redis.hget("geonames.admin1", f"{base[1]}.{base[2]}").decode("utf-8")
        admin2 = self.redis.hget("geonames.admin2", f"{base[1]}.{base[2]}.{base[3]}").decode("utf-8")

        # return [base[0], detail[0], admin2, admin1, cinfo["name"]]
        return [base[0], admin2, admin1, cinfo["name"]]


if __name__ == "__main__":
    geonames = GeoNamesRedis()
    geonames.database_cleanup()

    countries = geonames.countries_from_continent("EU", ["RU"])

    geonames.countries_download(countries)
    geonames.basecodes()

    for country in countries:
        geonames.country_process(country)

    query = geonames.resolv(50.564268, 5.801432)
    print(query)
