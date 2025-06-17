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
""", (device_id,int(time.time()),poll_batch_id,compressed_data))
            await db.commit()
    
    #getpendingdata

    async def get_pending_data(self,limit):
        """Get the Data back to send to aggregator when connection available"""
        # async with aiosqlite.connect(self.db_path) as db:
        #     #! this data is the pointing to the result set in the DB
        #     #! have to bring that all using this ptr
        #     data = await db.execute("Select id,device_id,timestamp,oid_data from temp_snmp_data WHERE status = 'pending' LIMIT ?", (limit,))
        # return await data.fetchall()

        #! lets try a better arch
        async with aiosqlite.connect(self.db_path) as db:
            cursor_data= await db.execute("SELECT id, device_id,timestamp,oid_data,status FROM temp_snmp_data WHERE status = 'pending' LIMIT ?",(limit,))
            collected_data = await cursor_data.fetchall()

            if(collected_data):
               id_list = [[row[0] for row in collected_data]]
               placeholder = ",".join('?' * len(id_list))

               await db.execute(f"UPDATE temp_snmp_data SET status = 'in_progress' WHERE id IN ({placeholder}) ", id_list)

               await db.commit()
            
            return collected_data

      
    
 





    #mark_as_sent

    #deletign old datas
            





