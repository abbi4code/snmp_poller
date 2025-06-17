import asyncio
import time 
import json #(we will need this later when we use zeroMQ)
import zmq.asyncio

from async_snmp import AsyncSNMPClient


class Device:
    def __init__(self,device_config,aggregator_config, storage):
        """
        Initialize the devicePoller

        Args:
            device_config (dict): configg for specefic device
                        eg: hostname, community,version, port
            aggregator_config (dict): config for agggre (like address,port  where data should be sent)

        """
        self.hostname = device_config["hostname"]
        self.port = device_config.get("port",161)
        self.community = device_config.get("community","public")
        self.version = device_config.get("version",2)

        self.client = AsyncSNMPClient(
            hostname= self.hostname,
            port= self.port,
            community= self.community,
            version=self.version
        )
        self.storage = storage

        self.aggregator_address = aggregator_config.get("address","localhost")
        self.aggregator_port = aggregator_config.get("port",5555)
        print(f"device Poller initialize for {self.hostname}:{self.port}")
        self.context = zmq.asyncio.Context()

        self.push_socket = self.context.socket(zmq.PUSH)

        self.push_socket.connect(f"tcp://{self.aggregator_address}:{self.aggregator_port}")
        print(f"device poller for {self.hostname} PUSH socket connected to tcp://{self.aggregator_address}:{self.aggregator_port}")

        print(f"DevicePoller initialized for {self.hostname}:{self.port}")

    
    
    async def poll_device(self):

        print(f"Polling for device with hostname {self.hostname}")

        try:
            data = {
                "hostname": self.hostname,
                "timestamp": int(time.time()),
                "data": {}
            }

            sys_descr_oid = "1.3.6.1.2.1.1.1.0"
            sys_name_oid = "1.3.6.1.2.1.1.5.0" 
            sys_uptime_oid = "1.3.6.1.2.1.1.3.0"

            result = await asyncio.gather(
                self.client.get(sys_descr_oid),
                self.client.get(sys_name_oid),
                self.client.get(sys_uptime_oid),
                return_exceptions = True 
            )
            

            data["data"]["sys_desc"] = result[0] if not isinstance(result[0], Exception) else str(result[0]) 
            data["data"]["sys_name"] = result[1] if not isinstance(result[1], Exception) else str(result[1])
            data["data"]["sys_uptime"] = result[2] if not isinstance(result[2], Exception) else str(result[2])

            interface_name_prefix = "1.3.6.1.2.1.2.2.1.2"   
            interface_status_prefix = "1.3.6.1.2.1.2.2.1.8"
            

            interface_descriptions_raw = await self.client.walk(interface_name_prefix)
            interface_statuses_raw = await self.client.walk(interface_status_prefix)

            data["data"]["interfaces"] = {}

            if interface_descriptions_raw:
                for items in interface_descriptions_raw.items():
                    oid,name = items
                    if_index = oid.split(".")[-1]
                    if if_index not in data["data"]["interfaces"]:
                        data["data"]["interfaces"][if_index] = {}
                    data["data"]["interfaces"][if_index]["name"] = name
            
            if interface_statuses_raw:
                for items in interface_statuses_raw.items():
                    oid,status = items
                    if_index = oid.split(".")[-1]
                    if if_index not in data["data"]["interfaces"]:
                        data["data"]["interfaces"][if_index] = {}
                    data["data"]["interfaces"][if_index]["status"] = status  
            for if_index in data["data"]["interfaces"]:
                if "name" not in data["data"]["interfaces"][if_index]:
                    data["data"]["interfaces"][if_index]["name"] = "N/A"
                if "status" not in data["data"]["interfaces"][if_index]:
                    data["data"]["interfaces"][if_index]["status"] = "N/A"
            
            print(f"successfully polled {self.hostname}. datas: sysName: {data['data'].get('sys_name')} ")
            return data
        except Exception as e:
            print(f"Error while polling device: {self.hostname}: {e}")

            return {
                "hostname": self.hostname,
                "timestamp": int(time.time()),
                "error": str(e),
                "data": {}
            }
    
    async def send_to_aggregator(self,data):

        try:
            await self.push_socket.send_json(data)
            

            print(f"send data for {self.hostname} to aggregator via zeroMQq")


        
        except Exception as e:
            print(f"Error while sending data to aggregator: err: {e}")


    #! for now, lets test it out here
    async def poll_and_fallback(self):
        """ Poll that data & check aggregator then either send or save in temp blob form"""
        polled_data = await self.poll_device()


        if polled_data and "error" not in polled_data:
            try:
                await self.send_to_aggregator(polled_data)
            except Exception as e:
                poll_batch_id = f"{self.hostname}_{int(time.time())}"
                await self.storage.store_offline(device_id = self.hostname, polled_data = polled_data, poll_batch_id = poll_batch_id)
        elif polled_data and "error" in polled_data:
            print(f"didnt send data for {self.hostname} due to polling error: {polled_data['error']}")
        else:
            print("No data from polled_device")


    async def poll_and_send(self):
        """ poll the device and send the data to aggregator"""
        #first, just poll the device
        polled_data = await self.poll_device()

        if polled_data and "error" not in polled_data:
            await self.send_to_aggregator(polled_data)
        elif polled_data and "error" in polled_data:
            print(f"didnt send data for {self.hostname} due to polling error: {polled_data['error']}")
        else:
            print("No data from polled_device")

    async def close_zmq(self):
        """ closing the push_socket n context """

        print(f"closing the zmq resources for {self.hostname}")
        if self.push_socket:
            self.push_socket.close()

