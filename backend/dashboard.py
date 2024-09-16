import asyncio
import websockets
import json
import redis
import time
import traceback

class DashboardSlave():
    def __init__(self, name, backlog=True):
        self.name = name
        self.backlog = backlog
        self.redis = redis.Redis()
        self.channel = "dashboard"

        self.payload = {}
        self.session = {}

        self.lastbeat = 0
        self.heartbeat = 30

        if self.backlog:
            self.restore()

    def restore(self):
        data = self.redis.get(f"{self.channel}-backlog-{self.name}")
        if data is not None:
            self.payload = json.loads(data.decode("utf-8"))

    def export(self):
        backlog = json.dumps(self.payload)
        self.redis.set(f"{self.channel}-backlog-{self.name}", backlog)


    def alive(self):
        message = {
            "id": self.name,
            "alive": True,
        }

        self.redis.publish(self.channel, json.dumps(message))
        self.lastbeat = time.time()


    def get(self, key):
        if key in self.payload:
            return self.payload[key]

        return None

    def set(self, key, value):
        self.payload[key] = value
        self.session[key] = value


    def commit(self):
        if len(self.session) == 0:
            if self.lastbeat + self.heartbeat > time.time():
                # nothing to push, no keep-alive needed now
                return

            return self.alive()

        message = {
            "id": self.name,
            "payload": self.session,
        }

        self.redis.publish(self.channel, json.dumps(message))

        self.session = {}
        self.lastbeat = time.time()
        self.export()

class DashboardServer():
    def __init__(self):
        print("[+] initializing dashboard backend server")

        self.wsclients = set()
        self.backlogs = {}
        self.channel = "dashboard"

        self.redis = redis.Redis()
        self.restore()

    def restore(self):
        prefix = f"{self.channel}-backlog-"
        skiplen = len(prefix)

        for back in self.redis.keys(f"{prefix}*"):
            channel = back.decode("utf-8")
            id = channel[skiplen:]

            print(f"[+] restoring backlog [{id}] from: {channel}")

            data = self.redis.get(channel)
            self.backlogs[id] = json.loads(data.decode("utf-8"))

    async def wsbroadcast(self, type, payload):
        if not len(self.wsclients):
            return

        for client in list(self.wsclients):
            if not client.open:
                continue

            content = json.dumps({"type": type, "payload": payload})

            try:
                await client.send(content)

            except Exception:
                traceback.print_exc()

    async def wspayload(self, websocket, type, payload):
        content = json.dumps({"type": type, "payload": payload})
        await websocket.send(content)

    async def handler(self, websocket, path):
        self.wsclients.add(websocket)

        print("[+] websocket: client connected")

        try:
            for id in self.backlogs:
                print(f"[+] sending backlog: {id}")
                await self.wspayload(websocket, id, self.backlogs[id])

            while True:
                if not websocket.open:
                    break

                await asyncio.sleep(1)

        finally:
            print("[+] websocket: client disconnected")
            self.wsclients.remove(websocket)

    async def redisloop(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(['dashboard'])

        while True:
            message = pubsub.get_message()
            # print(message)

            if message and message['type'] == 'message':
                handler = json.loads(message['data'])


                if "alive" in handler:
                    print("[+] heart beat from: %s" % handler['id'])

                    # keep-alive frame
                    await self.wsbroadcast(handler["id"], {})

                if "payload" in handler:
                    print("[+] forwarding data from slave: %s" % handler['id'])

                    # caching payload
                    id = handler['id']

                    if id not in self.backlogs:
                        self.backlogs[id] = {}

                    # partial backlog update
                    for key in handler["payload"]:
                        self.backlogs[id][key] = handler["payload"][key]

                    # forwarding
                    await self.wsbroadcast(handler["id"], handler["payload"])

            await asyncio.sleep(0.1)

    def run(self):
        # standard polling handlers
        loop = asyncio.get_event_loop()
        loop.set_debug(True)

        # handle websocket communication
        websocketd = websockets.serve(self.handler, "0.0.0.0", 30900)
        asyncio.ensure_future(websocketd, loop=loop)
        asyncio.ensure_future(self.redisloop(), loop=loop)

        print("[+] waiting for clients or slaves")
        loop.run_forever()

if __name__ == '__main__':
    dashboard = DashboardServer()
    dashboard.run()
