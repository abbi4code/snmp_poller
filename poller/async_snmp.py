import asyncio
from pysnmp.hlapi.asyncio import (SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd,nextCmd)


class AsyncSNMPClient:
    
    def __init__(self, hostname, port =161,community="public",version=2):
        self.hostname = hostname
        self.community = community
        # mpModel=0 for SNMPv1, mpModel=1 for SNMPv2c/SNMPv3
        self.mp_model = 1 if version >=2 else 0
        self.port = port
        self.engine = SnmpEngine()
        
    
    async def get(self,oid):
        """get a SNMP value for one oid (will add mroe later)"""
        
        # ^Look out for its str
        community_data = CommunityData(self.community,mpModel = self.mp_model)
        # defining the port target like means which port on the hostname to target for 
        #if below not works use this (got this in doc)
        #this below works on the latest pysnmp version but this version incompatible with snmpsim (will replace if got real network device access)
        #UdpTransportTarget.create(self.hostname, 161)
        transport_target = UdpTransportTarget((self.hostname,self.port), timeout =10, retries = 3)
        
        error_indication, error_status, error_index, var_binds = await getCmd(self.engine,community_data,transport_target,ContextData(), ObjectType(ObjectIdentity(oid)))
        
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
            return var_binds[0][1].prettyPrint()
        
        # & Will implement this later
    async def walk(self,oid_prefix):
        """ walk the oid tree starting from the given oid_prefix"""
        #! like here we are taking oid_prefix instead of taking a complete single oid
        # ^ so this will bring us all related oids data right that start with that same prefix
            
        result = {}
            
        community_data = CommunityData(self.community,mpModel =self.mp_model)
        
        transport_target = UdpTransportTarget((self.hostname,self.port),timeout = 10, retries = 3)
        
        # bulkCmd best for SNMPv2c/v3
        # but for v1c we can use nextCmd
        if self.mp_model == 0:
            # basic implementation of snmpv1c 
            # althrough proper walk in it will need more logic to detect end-of-mib
            print(f"have still to add more logic in it for {self.hostname}")
            current_oid = oid_prefix
            while True:
                error_indication,error_status,error_index,var_bind_table = await nextCmd(self.engine,community_data,transport_target,ContextData,ObjectType(ObjectIdentity(current_oid)))
                
                if error_indication or error_status or not var_bind_table:
                    print(f"errors while polling for hostname {self.hostname}: error: {error_indication or error_status}")
                    break
                # nextCmd usually returns one varBind
                var_bind = var_bind_table[0]
                
                #!couple of doubts
                # like here oid vs prefix (in structure) i want to visualize
                # also like you are assigning the return oid with prefix, wont this cause problem as this oid will a complete oid right as far i think (like i am thinking that oid are complete oid while predix are short one) so if here at last we assign the cucrent oid to this return oid, we wont be getting more oid with tthe prefix right, this will now return oid taht compelte match with this return oid
                oid, value = var_bind
                
                if not str(oid).startswith(oid_prefix):
                    print(f"Incorrect return oid for our prefix_oid: {current_oid}")
                    break
                
                #! here explain like i want to visualize the var_bind earlier vs now var_bind_table in real also this reulst like what storing in this how data looks here, also what below we are doing also
                #! here we are not pushing data right, as result is empty initailly still how we are doign result[str(oid)]
                result[str(oid)] = value.prettyPrint()
                
                current_oid = oid
                
            
            return result
        
            
    
async def test_snmp_get():
    # will use the config for device details later
    # for noww using just hardcoded
    
    snmp_hostname = "127.0.0.1"
    snmp_port = 1161
    
    client = AsyncSNMPClient(hostname=snmp_hostname,port = snmp_port ,community="public",version=2)
    
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
            