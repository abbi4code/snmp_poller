import asyncio
import zlib 
import aiosqlite
import json
import time

class OfflineStorage():
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize_db()

    async def initialize_db(self):
        """ Test schema """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
CREATE TABLE IF NOT EXISTS temp_snmp_data (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             device_id TEXT NOT NULL,
                             timestamp INTEGER NOT NULL,
                             poll_batch_id TEXT NOT NULL,
                             oid_data BLOB NOT NULL,
                             retry_count INTEGER DEFAULT 0,
                             status TEXT DEFAULT 'pending',
                             created_at INTEGER DEFAULT (strftime('%s', 'now'))
                             )
""")
            await db.commit()
    
    async def store_offline(self, device_id,polled_data,poll_batch_id):
        """ Storing data offline if not aggregator connection found"""
        #converting to json string then to bytes 
        compressed_data = zlib.compress(json.dumps(polled_data).encode("utf-8"))
        print(f"compressed_data: {compressed_data}")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
INSERT INTO temp_snmp_data (device_id,timestamp,poll_batch_id,oid_data) VALUES (?,?,?,?)
""", device_id,int(time.time(),poll_batch_id,compressed_data))
            await db.commit()
    
    #getpendingdata

    #mark_as_sent

    #deletign old datas
            





