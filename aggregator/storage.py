#here more logics to store the historal data as well
# or i think better to manege this logic at server lv at switchmap
# as this would be too much overhead for sqlite r8

import aiosqlite # for async sqllite ops
import json 
import os #to create the data dir

class DeviceStorage:
    def __init__(self, db_path):
        """
        initialze the device storage
        this db_path would be ./data/device.db
        """
        self.db_path = db_path
        print(f"database path set to {self.db_path}")

# some questions 
#are we creating tables for each device like for each hostname
# or for each aggregator(as for there is only one aggregator)
#althrough there is one more layer of zone in swithcmap too

    async def initialize(self):
        """
        this will initialzie the database and create tables if they dont exist
        this would be called once when the aggregator starts

        """
        print("storage: Initializing db")

        #creating dir for db file if not exist
        # os.path.dirname(self.db_path) get the dir path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        #async with ensures that db connection is properly  clased
        async with aiosqlite.connect(self.db_path) as db:
            # here our dataa
            # --- devices table----
            #gen info abotu each device
            # hostname: unique identifier for the device (PRIMARY_KEY)
            # last_updated: timestamp of lst successfull poll
            # system_dec, system_name, uptime (SNMP datas)
            await db.execute('''
              CREATE TABLE IF NOT EXISTS devices(
                            hostname TEXT PRIMARY KEY,
                            last_updated INTEGER,
                            system_description TEXT,
                            system_name TEXT,
                            uptime TEXT
                            )
 
            ''')
            print("Device table created ")

            # ---interface table----
            #stores info abotu each network interface on a  device
            #id : for each interface entry (unique,auto inc)
            #hostname: links this interface to a device in devices table (foreign key)
            #if_index: snmp interface index
            #name: interface desc/name
            #status operatoinal status (like for up = 1, down = 2)
            # last_updated: timestamp for a specefic interface data

            await db.execute('''
                CREATE TABLE IF NOT EXISTS interfaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT,
                    if_index TEXT,
                    name TEXT,
                    status TEXT,
                    last_updated INTEGER,
                    FOREIGN KEY (hostname) REFERENCES devices (hostname)
                    )
            ''')

            print("Interface table created")

            #save the changes to db file
            await db.commit()
        
        print("databse initialization completes")
    
    async def store_device_data(self,data):
        """
        stores the device info and interface info 

        data_str: 
        {
            "hostname": "abhishek_device",
            "timestamp": 1233546732,
            "data":{
                "system_description": "..",
                "system_name":"..",
                "uptime": "342"
                "interfaces":{
                    "1" : {"name" : "eth0", "status": "up(1)" },
                    "2" : {"name" : "eth1", "status": "down(1)" },
                }
            }

        }
        """
        hostname = data["hostname"]
        timestamp = data["timestamp"]

        device_specific_data = data.get("data", {})

        print(f"storing data for device with {hostname}, timestamp: {timestamp}")

        # lets store the device info first 

        async with aiosqlite.connect(self.db_path) as db:
            #update or insert device info
            #what if i want to store historical data as well (as discussed in the proposal)
            #INSERT or REPLACE: if a device with this hostname already exist 
            #records will be updated, or new will be inserted
            await db.execute('''
                        INSERT OR REPLACE INTO devices (hostname, last_updated, system_description,system_name,uptime )
                             VALUES (?,?,?,?,?)
                            ''', (
                                hostname,
                                timestamp,
                                device_specific_data.get("system_description"),
                                device_specific_data.get("system_name"),
                                device_specific_data.get("uptime")
                            ))
            print(f"device data stored for device: {hostname}")
            
            # --- update interface information ---
            if "interfaces" in device_specific_data and device_specific_data["interfaces"]:
                #first, deleling all existing interfaces entries for this hostname
                #this is simplest way to handle changes: del old & add new
                #comma to make it a tuple even with one item
                await db.execute("DELETE FROM interfaces WHERE hostname = ?",(hostname,))
                
                print(f"deleted old interfaces for {hostname}")

                interfaces_to_insert = []
                for if_index,interface_details in device_specific_data["interfaces"].items():
                    interfaces_to_insert.append((hostname,if_index,interface_details.get("name"),interface_details.get("status"),timestamp
                ))
                
                await db.executemany('''
                            INSERT INTO interfaces (hostname,if_index,name,status,last_updated) VALUES (?,?,?,?,?)
                   ''',interfaces_to_insert)
                
                print(f"Inserted {len(interfaces_to_insert)} new interface for {hostname}")
            else:
                print(f"Interfaces data not found in the data for {hostname}")
            
            await db.commit()
        print(f"Successfully stored data for hostname:{hostname}")
                
