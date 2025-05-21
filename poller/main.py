# soo here first we create a instance for each hostname okay
# then we get the polled the polled data from each hostname that we can print
# also here we will use asyncio.gather again to polled devices concurrently
# we need to first parse the config file (first we have find the path then have ro read )

import asyncio
import yaml
import os 

from .device import Device

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

    pollers = []

    if not config["poller"]["devices"]:
        print("No devices are there in poller.devices")
        return
    
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
        poller = Device(
            device_config = each_device,
            aggregator_config = aggregator_cfg_for_poller
        )
        #now we are just inserting the data from each devices 
        pollers.append()
    
    if not pollers:
        print("No valid device pollers could be created")
        return
    
    # nwo lets poll all devices concurrently 
    
    






        
