import yaml
import asyncio
import os


from collector import Collector

async def main():

    config_path = "config/config.yml"

    aggregator_config = {}

    try:
        with open(config_path, "r") as f:
            full_config = yaml.safe_load(f)
        if full_config and "aggregator_server" in full_config:
            aggregator_config = full_config["aggregator_server"]
            print("aggregator configuration loaded successfully")
        else:
            print("error in loading aggregator config, Using def config now")
            aggregator_config = {
                "address":"*",
                "port": 5555,
                "storage": {"path": "./data/devices.db"}
            }
    except FileNotFoundError:
        print(f"Config not found at {config_path}")
    except yaml.YAMLError as e:
        print(f"error while parsing the config")
    except Exception as e:
        print("unexpected err while loading configg")
    
        