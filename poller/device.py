import asyncio
import time 
# import json (we will need this later when we use zeroMQ)
#import zmq.asyncio

from async_snmp import AsyncSNMPClient

class Device:
    def __init__(self,device_config,aggregator_config):
        """
        Initialize the devicePoller

        Args:
            device_config (dict): configg for specefic device
                        eg: hostname, community,version, port
            aggregator_config (dict): config for agggre (like address,port  where data should be sent)

        """
        # can you here visualize the str how does device_config is will be looking 

        # maybe here we are using .get in case for adding a def value
        self.hostname = device_config["hostname"]
        self.port = device_config.get["port",161]
        self.community = device_config.get["community","public"]
        self.version = device_config.get["version",2]

        self.client = AsyncSNMPClient(
            hostname= self.hostname,
            port= self.port,
            community= self.community,
            version=self.version
        )

        self.aggregator_address = aggregator_config["address"]
        self.aggregator_port = aggregator_config["port"]
        print(f"device POller initialize for {self.hostname}:{self.port}")
    
    async def poll_device(self):

        print(f"Polling for device with hostname {self.hostname}")

        try:
            data = {
                "hostname": self.hostname,
                "timestamp": int(time.time()),
                "data": {}
            }

            # we will use asyncio.gather to fetch these concurrently
            sys_descr_oid = "1.3.6.1.2.1.1.1.0"
            sys_name_oid = "1.3.6.1.2.1.1.5.0" 
            sys_uptime_oid = "1.3.6.1.2.1.1.3.0"

            result = await asyncio.gather(
                # why used get here, so even in scalable system get used ??
                self.client.get(sys_descr_oid),
                self.client.get(sys_name_oid),
                self.client.get(sys_uptime_oid),
                return_exceptions = True #so even if one fail, it wont stopp
            )
            
            #use of isintance liek how does it work 

            data["data"]["sys_desc"] = result[0] if not isinstance(result[0], Exception) else str(result[0]) 
            data["data"]["sys_name"] = result[1] if not isinstance(result[1], Exception) else str(result[1])
            data["data"]["sys_uptime"] = result[2] if not isinstance(result[2], Exception) else str(result[2])


            # like for interface descriptions (ifDesc)
            #  and interference operational status (ifOperStatus)
            # first of all above there no prefix, but here there are prefix, is that because they are specefic to the device only, so they are unique, but there are datas that device itself generate, so there could be same type of data for a data type is that it, expline here more

            if_descr_prefix = "1.3.6.1.2.1.2.2.1.2"   
            if_oper_status_prefix = "1.3.6.1.2.1.2.2.1.8"
            
            # two things we have to keep in mind (in switchmap we have to do combine walk(prepare your logic ))
            # here, we will do two sep walks then parse 

            interface_descriptions_raw = await self.client.walk(if_descr_prefix)
            interface_statuses_raw = await self.client.walk(if_oper_status_prefix)

            data["data"]["interfaces"] = {}

            #visualize this in the real data to get the idea
            if interface_descriptions_raw:
                for items in interface_descriptions_raw.items():
                    oid,name = items
                    # what is this if_index at all and why -1, and is this everywhere foudn ?
                    if_index = oid.split(".")[-1]
                    if if_index not in data["data"]["interfaces"]:
                        data["data"]["interfaces"][if_index] = {}
                    data["data"]["interfaces"][if_index]["name"] = name
            
            if interface_statuses_raw:
                for items in interface_statuses_raw.items():
                    oid,status = items
                    if_index = oid.split(".")[-1]
                    if if_index not in data["data"]["interfaces"]:
                        # this could happen if an interface has a status but 
                        # no description (unlikely but possible)
                        data["data"]["interfaces"][if_index] = {}
                    data["data"]["interfaces"][if_index]["status"] = status

            # but how will do in switchmap (with that much amount of datas ) 
            # here, for now did a basic handling still not prod lv   
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
