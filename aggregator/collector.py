import asyncio
import zmq.asyncio
import json


class Collector:
    def __init__(self, aggregator_config):
        self.address = aggregator_config.get("address","localhost")
        self.port = aggregator_config.get("port", 5555)

        self.context = zmq.Context()
        self.pull_socket = self.context.socket(zmq.PULL)

        self.pull_socket.bind(f"tcp://{self.address}:{self.port}")

        print(f"aggregator pull socket now listening for address: {self.address} on port: {self.port}")

    async def initialize(self):
        """ will initialize the data needed by collector """
        # here will initialize those storages later (for now just chekc if pull socket works or not)
        print("aggre: dataCollector initialize")
        pass

    async def pull_data(self):

        print(f"pulling data from tcp://{self.address}:{self.address}")

        try:
            # so will be polling lets say 3 push_socket have send the data so all of them get into queue, so we are pullign them all at ones
            # by a single pulling socket ???
            while True:
                data = await self.pull_socket.recv_json()

                hostname= data.get("hostname","unknown host")
                timestamp = data.get("timestamp", "N/A")

                print(f"Recieved data from {hostname} at {timestamp}")
                # learn more parameters (including indent)
                print(json.dumps(data,indent=2))

                #we will store this data later on
                




