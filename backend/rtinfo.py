import requests
import time
import dashboard
import traceback
import sys

class MagibuxRtinfo:
    def __init__(self):
        self.dashboard = dashboard.DashboardSlave("rtinfo")

    def monitor(self):
        while True:
            sys.stdout.write("[+] rtinfo: fetching ... ")

            try:
                response = requests.get("http://127.0.0.1:8089/json", timeout=2)
                data = response.json()
                nodes = len(data["rtinfo"])

                print(f"{nodes} hosts found")

                self.dashboard.set("rtinfo", data["rtinfo"])
                self.dashboard.commit()

            except Exception:
                print("")
                traceback.print_exc()

            time.sleep(1)

if __name__ == "__main__":
    rtinfo = MagibuxRtinfo()
    rtinfo.monitor()
