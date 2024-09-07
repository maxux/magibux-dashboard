import requests
import dashboard
import traceback

slave = dashboard.DashboardSlave("rtinfo")

while True:
    print("[+] rtinfo: fetching")

    try:
        response = requests.get("http://127.0.0.1:8089/json", timeout=2)
        slave.set(response.json())

        print("[+] rtinfo: %d hosts found" % len(slave.payload['rtinfo']))

        slave.publish()

    except Exception:
        traceback.print_exc()

    slave.sleep(1)
