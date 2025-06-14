# soo here first we create a instance for each hostname okay
# then we get the polled the polled data from each hostname that we can print
# also here we will use asyncio.gather again to polled devices concurrently
# we need to first parse the config file (first we have find the path then have ro read )

import asyncio
import yaml
import os 
import zmq.asyncio
import zmq

from device import Device


async def main():

    config_path = "config/config.yaml"

    try:
        #getting the file then parsing it in pyobjectt
        with open(config_path,"r") as file_info:
            config = yaml.safe_load(file_info)
        print("Config loaded successfully")
    except FileNotFoundError:
        print(f"Err: config file not found at path: {config_path}")
        print("check if the config path is set correctly")
    except yaml.YAMLError as e:
        print(f"Err: not able to parse the config file: {e}")
    except Exception as e:
        print("Error while loading the config file")
    
    if not config or "poller" not in config or "devices" not in config["poller"]:
        print("Some configs are missing from config file either poller or devices")
        return 
    
    # now if everything good, yeahhh we can move to taking out all the devices

    # ! Currently we are created one poller for each device (we can fix the no of pollers later if needed)
    pollers = []

    if not config["poller"]["devices"]:
        print("No devices are there in poller.devices")
        return
    
    # like if want to have a single zmq context for all the pollers
    # like if we want to share context 
    #zmq_context = zmq.asyncio.Context() 

    

    for each_device in config["poller"]["devices"]:
        if "hostname" not in each_device:
            print(f"skipping this device as no hostname found for it in the config")
            continue
        # althrough we haev checked that poller will exist or not earlier
        aggregator_cfg_for_poller = config.get("poller",{}).get("aggregator",{})

        if not aggregator_cfg_for_poller:
            print(f"aggregator config for poller not found in the config file")
            print("Moving with default aggregator config, but sending data can fail here (check the def)")

            aggregator_cfg_for_poller = {"address": "localhost", "port": 5555}

        # here we are just creating a instance for each devices 
        # not called for polling here
        #<----here we can pass that context (it would be a central context)
        poller = Device(
            device_config = each_device,
            aggregator_config = aggregator_cfg_for_poller
        )
        #now we are just inserting the data from each devices 
        pollers.append(poller)
    
    if not pollers:
        print("No valid device pollers could be created")
        return
    
    # nwo lets poll all devices concurrently 

    # so calling (poll_device() for each poller)
    # what is this doing here, also i have confusion are we calling each poller for each device (means 1 poller for per device)
    # CHECK the architecture of switchmap how that handling this 
    # this gather all polling tasks and runs them concurrently

    #polling_tasks = [poller.poll_device() for poller in pollers]
    polling_tasks = [poller.poll_and_send() for poller in pollers]
    # like how does it looks is it like we are appending data from each hostname and appending this in this polling_task

    


    print(f"\nstarting to poll {len(pollers)} device(s)")

    #now here comes the confusion, as we already polled each device and get the data, why here we are polling again
    # i am seriously not understanding what going on here, how every dot is connecting

    # what is the use of that star also please explan me what its doing this whole thing
    await asyncio.gather(*polling_tasks)
    # what are coroutines anyways, i heard this work almost everywhere here

    print("\n<--Pollingggg completesss yayy --->")

    print(f"Poller: cleaning zeroMQ resources")
    for poller in pollers:
        await poller.close_zmq()

    # will test upper one first 
    # sharing a single context 
    # if zmq_context and not zmq_context.closed:
        # print("terminatingg")
        # zmq_context.term()

    # for device_data in all_devices_data:
    #     if device_data:
    #         if "error" in device_data:
    #             print(f"Error in fetching data for {device_data.get("hostname", "Unknown Hostname")}: error->{device_data["error"]}")
    #         else:
    #             print(f"Priting data for hostname: {device_data["hostname"]}")
               
    #             if "data" in device_data and device_data["data"]:
    #                 print(f"system_description: {device_data["data"]["sys_desc"]}")
    #                 print(f"system_name: {device_data["data"]["sys_name"]}")
    #                 print(f"system_uptime: {device_data["data"]["sys_uptime"]}")

    #                 if "interfaces" in device_data["data"] and device_data["data"]["interfaces"]:
    #                     print("printing each interfaces")

    #                     for if_index,if_info in device_data["data"]["interfaces"].items():
    #                         print(f"Index: {if_index}: Name: {if_info.get("name","N/A")} & status: {if_info.get("status","N/A")}")
    #                 else:
    #                     print("no interfaces found")
    #             else:
    #                 print("no data retrived")

    #     else:
    #         print("No device data found")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("process interrupted by user. goinggg down man")