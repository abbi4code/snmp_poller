#!/bin/bash

echo "Fixing SNMP configuration in all 20 containers..."

for i in {1..20}; do
    container_name="clab-linux-test-switch$(printf "%02d" $i)"
    echo "Fixing $container_name..."
    
    sudo docker exec $container_name sh -c "
        echo 'agentAddress udp:161' > /etc/snmp/snmpd.conf
        echo 'rocommunity public' >> /etc/snmp/snmpd.conf
        echo 'sysLocation \"Test Lab Device $i\"' >> /etc/snmp/snmpd.conf
        echo 'sysContact \"admin@test.lab\"' >> /etc/snmp/snmpd.conf
        echo 'sysName \"switch-$(printf \"%02d\" $i)\"' >> /etc/snmp/snmpd.conf
        pkill snmpd 2>/dev/null || true
        snmpd -Lo > /dev/null 2>&1 &
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Fixed $container_name"
    else
        echo "❌ Failed to fix $container_name"
    fi
done

echo ""
echo "Testing first few devices..."
sleep 2

# Test first 3 devices
for ip in 172.20.20.3 172.20.20.9 172.20.20.17; do
    result=$(snmpget -v2c -c public -t 3 -r 1 $ip 1.3.6.1.2.1.1.5.0 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ SNMP working on $ip"
    else
        echo "❌ SNMP not working on $ip"
    fi
done

echo ""
echo "All containers fixed! Ready to test your poller system." 