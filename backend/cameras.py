import requests
import dashboard

slave = dashboard.DashboardSlave("cameras")

while True:
    print("[+] cameras: fetching")

    try:
        response = requests.get("http://camera.magibux.maxux.net:10001/status.json", timeout=2)
        caminfo = response.json()

        slave.set(caminfo['camera_status'])

        print("[+] camera: %d cameras found" % len(slave.payload))

        slave.publish()

    except Exception as e:
        print(e)

    slave.sleep(10)
