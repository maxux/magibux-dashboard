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

    def set(self, value):
        self.payload = value

    def publish(self):
        self.redis.publish("dashboard", json.dumps({"id": self.name, "payload": self.payload}))

    def sleep(self, seconds):
        time.sleep(seconds)

class DashboardServer():
    def __init__(self):
        self.wsclients = set()
        self.payloads = {}
        self.redis = redis.Redis()

    #
    # Websocket
    #
    async def wsbroadcast(self, type, payload):
        if not len(self.wsclients):
            return

        goodcontent = json.dumps({"type": type, "payload": payload})

        for client in list(self.wsclients):
            if not client.open:
                continue

            content = json.dumps({"type": type, "payload": payload})

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
            for id in self.payloads:
                item = self.payloads[id]
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
                if "id" in handler['payload']:
                    id = "%s-%s" % (handler['id'], handler['payload']['id'])

                self.payloads[id] = {
                    "id": handler['id'],
                    "payload": handler['payload'],
                }

                # forwarding
                await self.wsbroadcast(handler['id'], handler['payload'])

            await asyncio.sleep(0.1)

    def run(self):
        # standard polling handlers
        loop = asyncio.get_event_loop()
        loop.set_debug(True)

        # handle websocket communication
        websocketd = websockets.serve(self.handler, "127.0.0.1", 30900)
        asyncio.ensure_future(websocketd, loop=loop)
        asyncio.ensure_future(self.redisloop(), loop=loop)

        print("[+] waiting for clients or slaves")
        loop.run_forever()

if __name__ == '__main__':
    dashboard = DashboardServer()
    dashboard.run()
