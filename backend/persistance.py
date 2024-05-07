import redis
import pymysql
import json
import time
from config import config

class MagibuxPersistance:
    def __init__(self):
        self.db = pymysql.connect(
            host=config['db-host'],
            user=config['db-user'],
            password=config['db-pass'],
            database=config['db-name'],
            autocommit=True
        )

        self.queue = redis.Redis()

    def temperature(self, message):
        source = message['source']
        value = int(message['value'] * 100)

        cursor = self.db.cursor()
        query = """
            INSERT INTO temperature_values (id, moment, value)
            SELECT id, CURRENT_TIMESTAMP, %s FROM temperature_devices WHERE path = %s
        """
        cursor.execute(query, (value, source))

    def pressure(self, message):
        source = message['source']
        value = int(message['value'] * 100)

        cursor = self.db.cursor()
        query = """
            INSERT INTO pressure_values (channel, moment, value)
            SELECT id, NOW(6), %s FROM pressure_channels WHERE path = %s
        """
        cursor.execute(query, (value, source))

    def process(self, message):
        print(message)

        if message['type'] == "temperature":
            self.temperature(message)

        if message['type'] == "pressure":
            self.pressure(message)

    def monitor(self):
        pubsub = self.queue.pubsub()
        pubsub.subscribe(['persistance'])

        print("[+] persistance: waiting data")

        while True:
            message = pubsub.get_message(timeout=10)

            if message == None:
                continue

            if message['type'] == "message":
                data = json.loads(message['data'])
                self.process(data)

if __name__ == "__main__":
    persistance = MagibuxPersistance()
    persistance.monitor()
