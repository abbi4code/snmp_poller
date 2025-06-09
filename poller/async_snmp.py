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
        # this will help in visualization
        # For SNMPv2c - use proper bulkCmd implementation
        var_binds = [ObjectType(ObjectIdentity(oid_prefix))]
        
        print(f"Starting bulk walk for {self.hostname} with prefix {oid_prefix}")
        
        while var_binds:
            error_indication, error_status, error_index, var_bind_table = await bulkCmd(
                self.engine, 
                community_data, 
                transport_target,
                ContextData(),
                0, 25,  # non-repeaters=0, max-repetitions=25
                *var_binds
            )
            
            if error_indication:
                print(f"Error while connecting to hostname {self.hostname} for prefix: {oid_prefix}: {error_indication}")
                break 
            elif error_status:
                print(f"SNMP walk error_status for hostname: {self.hostname} prefix: {oid_prefix}: {error_status}")
                break
            else:
               
                print(f"DEBUG: var_bind_table type: {type(var_bind_table)}, length: {len(var_bind_table) if var_bind_table else 0}")
                
                valid_binds = []
                for i, var_bind_row in enumerate(var_bind_table):
               
                    if not isinstance(var_bind_row, list) or len(var_bind_row) == 0:
                        print(f"DEBUG: Unexpected var_bind_row format: {var_bind_row}")
                        continue
                    
                  
                    obj_type = var_bind_row[0]
                    oid = obj_type[0] 
                    value = obj_type[1] 
                    
                    # Check for end of MIB first
                    if hasattr(value, 'tagSet') and 'EndOfMibView' in str(value):
                        print(f"DEBUG: End of MIB reached at OID: {oid}")
                        break
                    
                    # Check if we're still within our desired OID prefix
                    if not str(oid).startswith(oid_prefix):
                        print(f"DEBUG: OID {oid} is outside prefix {oid_prefix}, ending walk")
                        break
                    
                    # Store valid results
                    result[str(oid)] = value.prettyPrint()
                    valid_binds.append(oid)
                    print(f"DEBUG: Added {oid} = {value.prettyPrint()}")
                
                if not valid_binds:
                    print(f"DEBUG: No valid binds found, ending walk")
                    break
                
                last_oid = valid_binds[-1]
                
                # Instead of using the same OID, let's try to get the next one
                # by using nextCmd for a single step
                try:
                    next_error_indication, next_error_status, next_error_index, next_var_bind_table = await nextCmd(
                        self.engine, community_data, transport_target, ContextData(), 
                        ObjectType(ObjectIdentity(last_oid))
                    )
                    
                    if next_error_indication or next_error_status or not next_var_bind_table:
                        print(f"DEBUG: No next OID available after {last_oid}, ending walk")
                        break
                    
                    # Get the next OID to continue bulk walking from
                    next_oid = next_var_bind_table[0][0]
                    if str(next_oid).startswith(oid_prefix):
                        var_binds = [ObjectType(ObjectIdentity(next_oid))]
                        print(f"DEBUG: Next iteration will start from OID: {next_oid}")
                    else:
                        print(f"DEBUG: Next OID {next_oid} is outside prefix, ending walk")
                        break
                except Exception as e:
                    print(f"DEBUG: Error getting next OID: {e}, ending walk")
                    break
                    
        return result
            
# ------depreciated 🙂-----
# async def test_snmp_get():
#     # will use the config for device details later
#     # for noww using just hardcoded
    
#     snmp_hostname = "127.0.0.1"
#     snmp_port = 1161
    
#     client = AsyncSNMPClient(hostname=snmp_hostname,port = snmp_port ,community="public",version=2)
    
#     print(f"\n------------attempting to get system description (1.3.6.1.2.1.1.1.0) from {client.hostname}------")
    
#     system_description = await client.get("1.3.6.1.2.1.1.1.0")
    
#     if system_description:
#         print(f"System Description: {system_description}")
#     else:
#         print("Failed to get the sys desc")
    
#     print("\nAttempting to get the system Uptime (1.3.6.1.2.1.1.3.0)...")
    
#     system_uptime = await client.get("1.3.6.1.2.1.1.3.0")
    
#     if system_uptime:
#         print(f"System Uptime: {system_uptime}")
#     else:
#         print("Failed to get system Uptime")
        
#     print(f"\n testing WALK for if-mib interface table (1.3.6.1.2.1.2.2.1) from {client.hostname} ---")
    
#     interface_data = await client.walk("1.3.6.1.2.1.2.2.1")
    
#     print(f"Interface_data: {interface_data}")
    
#     if interface_data:
#         count = 0
        
#         for data in interface_data.items():
#             oid,value = data
#             print(f"{oid}: {value}")
            
#             count += 1
            
#             if count >= 10 and len(interface_data) > 10:
#                 print(".. and moree")
#                 break
#         if not interface_data:
#             print("no interface data found till here--")
#     else:
#         print("failed to get interface_data via walk")
            
    

# if __name__ == "__main__":
#     asyncio.run(test_snmp_get())
            