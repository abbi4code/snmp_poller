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
                            timestamp INTEGER
                            system_description TEXT,
                            system_name TEXT,
                            uptime TEXT
                            )
 
            ''')
            print("Device table created ")

            
