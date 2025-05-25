import yaml
import asyncio
import os
import signal


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
    
    collector = Collector(aggregator_config=aggregator_config)

    #gracefullyyy shutdown handling
    # know about all this man 
    loop =asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_handler():
        print("shutdown signal recieved......")
        stop_event.set()

    # mroe feat like triggering for ctrl + c
    try:
        loop.add_signal_handler(signal.SIGINT,shutdown_handler)
        loop.add_signal_handler(signal.SIGTERM,shutdown_handler)
    except NotImplementedError:
        print("sorry bruhh: signal handler not avail for your system, use ctrl + c instead")
        pass
    except NameError:
        try:
            loop.add_signal_handler(signal.SIGINT,shutdown_handler)
            loop.add_signal_handler(signal.SIGTERM,shutdown_handler)
        except Exception as e:
            print(f"could not set signal handler: {e}")
    
    collection_tasks = None
    try:
        await collector.initialize()
        print("Starting data collection")
        collection_tasks = asyncio.create_task(collector.pull_data())

        #keeping the main fn alive till stop_event 
        await stop_event.wait()
    except asyncio.CancelledError:
        print("main task cancelled")
    
    finally:
        print("Aggregator: Shutting down...")
        if collection_tasks and not collection_tasks.done():
            collection_tasks.cancel()
            try:
                await collection_tasks 
            except asyncio.CancelledError:
                print("Aggregator: Collection task successfully cancelled during shutdown.")
        
        
        if collector and collector.zmq_context and not collector.zmq_context.closed:
            print("Aggregator: Terminating ZeroMQ context.")
            collector.zmq_context.term()
        print("Aggregator: Exited.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aggregator: process intrupted by youuu mybro")

        