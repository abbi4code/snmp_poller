import asyncio
import zmq.asyncio
import json
import zmq

from storage import DeviceStorage
class Collector:
    def __init__(self, aggregator_config):
        self.address = aggregator_config.get("address","localhost")
        self.port = aggregator_config.get("port", 5555)

        self.context = zmq.asyncio.Context()
        self.pull_socket = self.context.socket(zmq.PULL)

        self.pull_socket.bind(f"tcp://{self.address}:{self.port}")

        # db_path= aggregator_config.get("sto")
        if "storage" not in aggregator_config or "path" not in aggregator_config["storage"]:
            print("database storage not configured")
            
            storage_path = "./data/devices.db"
            if "storage" in aggregator_config and "path" in aggregator_config["storage"]:
                 storage_path = aggregator_config["storage"]["path"]
            print(f"Aggregator WARNING: Using storage path '{storage_path}' (default or from config).")
        else:
            storage_path = aggregator_config["storage"]["path"]
        
        self.storage = DeviceStorage(db_path=storage_path)
        print("DeviceStorgae instance created")


        

        print(f"aggregator pull socket now listening for address: {self.address} on port: {self.port}")

    async def initialize(self):
        """ will initialize the data needed by collector """
        # here will initialize those storages later (for now just chekc if pull socket works or not)
        #this will create DB tables if they dont exist earlier
        await self.storage.initialize() 
        print("aggre: dataCollector initialize")

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

                if "error" not in data:
                    await self.storage.store_device_data(data=data)
                    print(f"Data for {hostname} should be stored now")
                else:
                    print(f"error while recieving data for hostname:{hostname}")
                #we will store this data later on
        except asyncio.CancelledError:
            print("collection task cancell")
        except Exception as e:
            print(f"err in collector loop: {e}")
        finally:
            print("shutting down collector")
            if self.pull_socket and not self.pull_socket.closed:
                self.pull_socket.closed()





