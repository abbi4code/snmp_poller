
import asyncio
import yaml
import os 
import zmq.asyncio
import zmq

from blobStorage import OfflineStorage

from device import Device


async def main():

    config_path = "config/config.yaml"
    db_path = "temp_polled_data/data.db"

    try:
        
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
    
    pollers = []

    if not config["poller"]["devices"]:
        print("No devices are there in poller.devices")
        return
    
    blob_storage = OfflineStorage(db_path=db_path)
    await blob_storage.ensure_initialization()


    

    for each_device in config["poller"]["devices"]:
        if "hostname" not in each_device:
            print(f"skipping this device as no hostname found for it in the config")
            continue
        aggregator_cfg_for_poller = config.get("poller",{}).get("aggregator",{})

        if not aggregator_cfg_for_poller:
            print(f"aggregator config for poller not found in the config file")
            print("Moving with default aggregator config, but sending data can fail here (check the def)")

            aggregator_cfg_for_poller = {"address": "localhost", "port": 5555}

        poller = Device(
            device_config = each_device,
            aggregator_config = aggregator_cfg_for_poller,
            storage = blob_storage
        )
    
        
        

        pollers.append(poller)
    
    if not pollers:
        print("No valid device pollers could be created")
        return
    polling_tasks = [poller.poll_and_fallback() for poller in pollers]

    print(f"\nstarting to poll {len(pollers)} device(s)")

    await asyncio.gather(*polling_tasks)

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