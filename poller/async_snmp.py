import asyncio
from pysnmp.hlapi.asyncio import (SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd,nextCmd, bulkCmd)


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
                oid, value = var_bind
                
                if not str(oid).startswith(oid_prefix):
                    print(f"Incorrect return oid for our prefix_oid: {current_oid}")
                    break
                
                result[str(oid)] = value.prettyPrint()
                
                current_oid = oid
                
            
            return result
        
        bulk_gen = await bulkCmd(self.engine, community_data, transport_target,ContextData(),0,25,ObjectType(ObjectIdentity(oid_prefix)))
        
        async for error_indication,error_status,error_index, var_binds_table in bulk_gen:
            
            if error_indication:
                print(f"Error while connecting to hostname {self.hostname} for prefix: {oid_prefix}")
                # hmm for simple can break on error
                # will add better error_handling here
                # as based on the err, we might just want to logg or maybe just continue 
                break 
            elif error_status:
                print(f"SNMP walk error_status for hostname: {self.hostname} prefix: {oid_prefix}")
                
                # ! below list of err handling we need to add later on 
                # ^ snmp errors (liek noSuchName if we wlk past the end of the table quickly)
                # ^ for a better check, we need to check if err means we are at the end of the MIB view
                break
            else:
                for var_bind in var_bind_table:
                    oid,value = var_bind
                    
                    # ! what about that case when we have multiple oid_prefix, then how we will handle think of the soln
                    if not str(oid).startswith(oid_prefix):
                        return result
                    # !what does here prettyPrint() does extra here, cant we do same without it 
                    result[str(oid)] = value.prettyPrint()
                    
        return result
            
async def test_snmp_get():
    # will use the config for device details later
    # for noww using just hardcoded
    
    snmp_hostname = "127.0.0.1"
    snmp_port = 1161
    
    client = AsyncSNMPClient(hostname=snmp_hostname,port = snmp_port ,community="public",version=2)
    
    print(f"\n------------attempting to get system description (1.3.6.1.2.1.1.1.0) from {client.hostname}------")
    
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
        
    print(f"\n testing WALK for if-mib interface table (1.3.6.1.2.1.2.2.1) from {client.hostname} ---")
    
    interface_data = await client.walk("1.3.6.1.2.1.2.2.1")
    
    print(f"Interface_data: {interface_data}")
    
    if interface_data:
        count = 0
        
        for data in interface_data.items():
            oid,value = data
            print(f"{oid}: {value}")
            
            count += 1
            
            if count >= 10 and len(interface_data) > 10:
                print(".. and moree")
                break
        if not interface_data:
            print("no interface data found till here--")
    else:
        print("failed to get interface_data via walk")
            
    

if __name__ == "__main__":
    asyncio.run(test_snmp_get())
            