import asyncio
import websockets
import json
import redis
import time

class DashboardSlave():
    def __init__(self, name):
        self.name = name
        self.redis = redis.Redis()
        self.payload = {}
        self.updated = None

    def set(self, value, updated=None):
        self.payload = value
        self.updated = updated

    def publish(self):
        message = {
            "id": self.name,
            "payload": self.payload,
            "updated": self.updated
        }

        self.redis.publish("dashboard", json.dumps(message))

    def sleep(self, seconds):
        time.sleep(seconds)

class DashboardServer():
    def __init__(self):
        self.wsclients = set()
        self.backlogs = {}
        self.redis = redis.Redis()

    async def wsbroadcast(self, type, payload, updated):
        if not len(self.wsclients):
            return

        for client in list(self.wsclients):
            if not client.open:
                continue

            stripped = payload

            if updated:
                stripped = {}
                stripped[updated] = payload[updated]

            content = json.dumps({"type": type, "payload": stripped})

            try:
                await client.send(content)

            except Exception as e:
                print(e)

    async def wspayload(self, websocket, type, payload):
        content = json.dumps({"type": type, "payload": payload})
        await websocket.send(content)

    async def handler(self, websocket, path):
        self.wsclients.add(websocket)

        print("[+] websocket: client connected")

        try:
            for id in self.backlogs:
                item = self.backlogs[id]
                print("[+] sending backlog: %s (%s)" % (id, item['id']))
                await self.wspayload(websocket, item['id'], item['payload'])

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

                print("[+] forwarding data from slave: %s" % handler['id'])

                # caching payload
                id = handler['id']
                """
                if "id" in handler['payload']:
                    id = "%s-%s" % (handler['id'], handler['payload']['id'])
                """

                self.backlogs[id] = handler

                # forwarding
                await self.wsbroadcast(handler['id'], handler['payload'], handler['updated'])

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
