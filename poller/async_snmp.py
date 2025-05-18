import asyncio
from pysnmp.hlapi.asyncio import (SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, get_cmd)


class AsyncSNMPClient:
    
    def __init__(self, hostname, community="public", version=2):
        self.hostname = hostname
        self.community = community
        # mpModel=0 for SNMPv1, mpModel=1 for SNMPv2c/SNMPv3
        self.mp_model = 1 if version >=2 else 0
        self.engine = SnmpEngine()
        
    
    async def get(self,oid):
        """get a SNMP value for one oid (will add mroe later)"""
        
        # ^Look out for its str
        community_data = CommunityData(self.community,mpModel = self.mp_model)
        # defining the port target like means which port on the hostname to target for 
        #if below not works use this (got this in doc)
        #UdpTransportTarget.create(self.hostname, 161)
        transport_target = await UdpTransportTarget.create((self.hostname,161), timeout =10, retries = 3)
        
        #* getCmd returns a coroutine generator 
        # ^ we have to go async here 
        error_indication, error_status, error_index, var_binds = await get_cmd(self.engine,community_data,transport_target,ContextData(), ObjectType(ObjectIdentity(oid)))
        
        if error_indication:
            print(f"Error getting in SNMP data from hostname:{self.hostname} OID: {oid}: {error_indication}")
            return None
        elif error_status:
            # ^ simple status error log
            print(
                f"SNMP GET error_status for {self.hostname} OID {oid}: {error_status.prettyPrint()} at "
                f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
            )
            return None
        else:
            #var_binds are list of tuples (OID,values)
            #for a get req, contains only one value
            #value wouldnt be in plain py type
            # why no [0][0] and what does this prettyPrint() do
            return var_binds[0][1].prettyPrint()
        
        # & Will implement this later
        async def walk(self,oid_prefix):
            raise NotImplementedError("Baad me karunga bro pehle ek device pe toh check karlu")
        

async def test_snmp_get():
    # will use the config for device details later
    # for noww using just hardcoded
    
    client = AsyncSNMPClient(hostname="demo.snmplabs.com", community="public",version=2)
    
    print(f"Attempting to get system description (1.3.6.1.2.1.1.1.0) from {client.hostname}")
    
    system_description = await client.get("1.3.6.1.2.1.1.1.0")
    
    if system_description:
        print(f"System Description: {system_description}")
    else:
        print("Failed to get the sys desc")
    
    print("\nAttempting to get the system Uptime (1.3.6.1.2.1.1.3.0)...")
    
    system_uptime = await client.get("1.3.6.1.2.1.1.3.0")
    
    if system_uptime:
        print(f"System Uptime: {system_uptime}")
    else:
        print("Failed to get system Uptime")
    

if __name__ == "__main__":
    asyncio.run(test_snmp_get())
            