import asyncio
import zlib 
import aiosqlite
import json
import time

#! add concise error handlign 

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

    async def get_pending_data(self, limit):
        """Get the Data back to send to aggregator when connection available"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor_data = await db.execute("SELECT id, device_id, timestamp, poll_batch_id, oid_data, status FROM temp_snmp_data WHERE status = 'pending' LIMIT ?", (limit,))
            collected_data = await cursor_data.fetchall()

            if collected_data:
                # Fix the id_list bug - remove extra brackets
                id_list = [row[0] for row in collected_data]
                placeholder = ','.join('?' * len(id_list))

                await db.execute(f"UPDATE temp_snmp_data SET status = 'in_progress' WHERE id IN ({placeholder})", id_list)
                await db.commit()
            
            # Decompress and decode the data before returning
            processed_data = []
            for row in collected_data:
                record_id, device_id, timestamp, poll_batch_id, compressed_oid_data, status = row
                
                try:
                    # Step 1: Decompress the compressed bytes
                    decompressed_bytes = zlib.decompress(compressed_oid_data)
                    
                    # Step 2: Decode bytes to string
                    json_string = decompressed_bytes.decode('utf-8')
                    
                    # Step 3: Parse JSON string back to Python object
                    oid_data = json.loads(json_string)
                    
                    # Return the record with decompressed data
                    processed_data.append({
                        'id': record_id,
                        'device_id': device_id,
                        'timestamp': timestamp,
                        'poll_batch_id': poll_batch_id,
                        'oid_data': oid_data,  # Now this is a proper Python dict/list
                        'status': status
                    })
                    
                except (zlib.error, json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error decompressing data for record {record_id}: {e}")
                    # You might want to mark this record as corrupted
                    continue
            
            return processed_data
    
    async def mark_as_sent(self, record_ids):
        """Deleting our already sent data"""
        if not record_ids:
            return
            
        placeholder = ','.join('?' * len(record_ids))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"DELETE FROM temp_snmp_data WHERE id IN ({placeholder})", record_ids)
            await db.commit()  # Fix: Add missing commit
    
    async def cleanup_old_data(self, days_old = 7):
        """ clean up old data to prevent disk space issues """
        cutoff_time = int(time.time()) - (days_old * 24 * 60 * 60)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"DELETE FROM temp_snmp_data WHERE timestamp < ?", (cutoff_time,))
            await db.commit()

    




      
    
 





    #mark_as_sent

    #deletign old datas
            





