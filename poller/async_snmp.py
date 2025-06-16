import asyncio
import time
from pysnmp.hlapi.asyncio import (SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd,nextCmd, bulkCmd)
from pysnmp.proto.errind import RequestTimedOut
from pysnmp.error import PySnmpError


class AsyncSNMPClient:
    
    def __init__(self, hostname, port=161, community="public", version=2, max_concurrent=10):
        self.hostname = hostname
        self.community = community
        # mpModel=0 for SNMPv1, mpModel=1 for SNMPv2c/SNMPv3
        self.mp_model = 1 if version >= 2 else 0
        self.port = port
        self.engine = SnmpEngine()
        
        self.stats = {
            'requests_sent': 0,
            'requests_failed': 0,
            'total_time': 0.0,
            'last_poll_time': None
        }
        
        # Rate limiting for scale
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def get(self, oid):
        """Get a SNMP value for one oid with performance tracking"""
        
        start_time = time.time()
        # just ratelmt
        async with self.semaphore:
            try:
                self.stats['requests_sent'] += 1
                
                community_data = CommunityData(self.community, mpModel=self.mp_model)
                transport_target = UdpTransportTarget((self.hostname, self.port), timeout=10, retries=3)
                
                error_indication, error_status, error_index, var_binds = await getCmd(
                    self.engine, community_data, transport_target, ContextData(), 
                    ObjectType(ObjectIdentity(oid))
                )
                
                if error_indication:
                    self.stats['requests_failed'] += 1
                    if isinstance(error_indication, RequestTimedOut):
                        print(f"TIMEOUT: SNMP request to {self.hostname} OID {oid} timed out")
                        return None
                    else:
                        print(f"ERROR: SNMP request to {self.hostname} OID {oid}: {error_indication}")
                        return None
                elif error_status:
                    self.stats['requests_failed'] += 1
                    print(f"SNMP GET error_status for {self.hostname} OID {oid}: {error_status.prettyPrint()} at "
                          f"{error_index and var_binds[int(error_index) - 1][0] or '?'}")
                    return None
                else:
                    result = var_binds[0][1].prettyPrint()
                    print(f"Result=>>>>>>>>>>>>>>>> {result}")
                    elapsed = time.time() - start_time
                    self.stats['total_time'] += elapsed
                    return result
                    
            except PySnmpError as e:
                self.stats['requests_failed'] += 1
                print(f"PySnmpError getting {oid} from {self.hostname}: {e}")
                return None
            except Exception as e:
                self.stats['requests_failed'] += 1
                print(f"Unexpected error getting {oid} from {self.hostname}: {e}")
                return None
                
    async def walk(self, oid_prefix):
        """Enhanced walk with better performance and error handling"""
        
        start_time = time.time()
        async with self.semaphore: 
            try:
                self.stats['requests_sent'] += 1
                result = {}
                
                community_data = CommunityData(self.community, mpModel=self.mp_model)
                transport_target = UdpTransportTarget((self.hostname, self.port), timeout=10, retries=3)
                
                if self.mp_model == 0:

                    return await self._walk_v1(oid_prefix, community_data, transport_target)
                else:
                    return await self._walk_v2(oid_prefix, community_data, transport_target)
                
            
                    
            except PySnmpError as e:
                self.stats['requests_failed'] += 1
                print(f"PySnmpError walking {oid_prefix} from {self.hostname}: {e}")
                return {}
            except Exception as e:
                self.stats['requests_failed'] += 1
                print(f"Unexpected error walking {oid_prefix} from {self.hostname}: {e}")
                return {}
            finally:
                elapsed = time.time() - start_time
                self.stats['total_time'] += elapsed
                
    async def _walk_v1(self, oid_prefix, community_data, transport_target):
        """Walk implementation for SNMPv1"""
        result = {}
        current_oid = oid_prefix
        max_iterations = 1000 
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            error_indication, error_status, error_index, var_bind_table = await nextCmd(
                self.engine, community_data, transport_target, ContextData(),
                ObjectType(ObjectIdentity(current_oid))
            )
            
            if error_indication or error_status or not var_bind_table:
                break
                
            var_bind = var_bind_table[0]
            oid, value = var_bind
            
            if not str(oid).startswith(oid_prefix):
                break
                
            result[str(oid)] = value.prettyPrint()
            current_oid = oid
            
        return result

    async def _walk_v2(self, oid_prefix, community_data, transport_target):
        """Enhanced walk implementation for SNMPv2c using bulkCmd"""
        result = {}
        var_binds = [ObjectType(ObjectIdentity(oid_prefix))]
        max_iterations = 100 
        iterations = 0
        
        while var_binds and iterations < max_iterations:
            iterations += 1

            error_indication, error_status, error_index, var_bind_table = await bulkCmd(
                self.engine, community_data, transport_target, ContextData(),
                0, 25, 
                *var_binds
            )
            
            if error_indication:
                print(f"SNMP WALK error for {self.hostname} prefix {oid_prefix}: {error_indication}")
                break
            elif error_status:
                print(f"SNMP WALK error_status for {self.hostname} prefix {oid_prefix}: {error_status}")
                break
                
            valid_binds = []
            for var_bind_row in var_bind_table:
                if not isinstance(var_bind_row, list) or len(var_bind_row) == 0:
                    continue
                    
                obj_type = var_bind_row[0]
                oid = obj_type[0]
                value = obj_type[1]

                # checking for end of MIB
                if hasattr(value, 'tagSet') and 'EndOfMibView' in str(value):
                    break
                    
                # checkingg if we're still within our desired OID prefix
                if not str(oid).startswith(oid_prefix):
                    break
                    
                result[str(oid)] = value.prettyPrint()
                valid_binds.append(oid)
                
            if not valid_binds:
                break
            
            # preparing for next iteration ->> continue from the last OID
            last_oid = valid_binds[-1]
            try:
                next_error_indication, next_error_status, next_error_index, next_var_bind_table = await nextCmd(
                    self.engine, community_data, transport_target, ContextData(),
                    ObjectType(ObjectIdentity(last_oid))
                )
                
                if next_error_indication or next_error_status or not next_var_bind_table:
                    break
                    
                next_oid = next_var_bind_table[0][0]
                if str(next_oid).startswith(oid_prefix):
                    var_binds = [ObjectType(ObjectIdentity(next_oid))]
                else:
                    break
            except Exception:
                break
                
        return result
        
    def get_stats(self):
        """Get performance statistics"""
        avg_response_time = 0
        if self.stats['requests_sent'] > 0:
            avg_response_time = self.stats['total_time'] / self.stats['requests_sent']
            
        success_rate = 0
        if self.stats['requests_sent'] > 0:
            success_rate = (self.stats['requests_sent'] - self.stats['requests_failed']) / self.stats['requests_sent'] * 100
            
        return {
            'hostname': self.hostname,
            'requests_sent': self.stats['requests_sent'],
            'requests_failed': self.stats['requests_failed'],
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_response_time, 3),
            'total_time': round(self.stats['total_time'], 3)
        }
        
    def reset_stats(self):
        """Reset performance statistics"""
        self.stats = {
            'requests_sent': 0,
            'requests_failed': 0,
            'total_time': 0.0,
            'last_poll_time': None
        }
            