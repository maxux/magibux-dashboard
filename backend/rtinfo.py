import requests
import importlib

dashboard = importlib.import_module("dashboard-rtinfo")
slave = dashboard.DashboardSlave("rtinfo")

while True:
    print("[+] rtinfo: fetching")

    try:
        response = requests.get("http://127.0.0.1:8089/json", timeout=2)
        slave.set(response.json())

        print("[+] rtinfo: %d hosts found" % len(slave.payload['rtinfo']))

        slave.publish()

    except Exception as e:
        print(e)

    slave.sleep(1)
