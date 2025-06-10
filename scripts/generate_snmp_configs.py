#!/usr/bin/env python3
"""
Generate SNMP configuration files for scale testing
"""

import os

def generate_snmp_configs(num_devices=20, output_dir="snmp-devices"):
    """Generate SNMP configuration files for multiple devices"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(1, num_devices + 1):
        config_content = f"""# SNMP Configuration for device {i}
agentAddress udp:161
rocommunity public

# System information
sysLocation    "Test Lab - Device {i}"
sysContact     "admin@testlab.com"
sysName        "switch-{i}"

# Interface simulation - simulating a 24-port switch
interface 1
interface 2
interface 3
interface 4
interface 5
interface 6
interface 7
interface 8
interface 9
interface 10
interface 11
interface 12
interface 13
interface 14
interface 15
interface 16
interface 17
interface 18
interface 19
interface 20
interface 21
interface 22
interface 23
interface 24

# SNMP logging
logTimestamp yes
"""
        
        filename = os.path.join(output_dir, f"snmpd-{i}.conf")
        with open(filename, 'w') as f:
            f.write(config_content)
        
        print(f"Generated {filename}")

def generate_config_yaml(num_devices=20, base_ip="172.20.20", start_ip=11):
    """Generate config.yaml with multiple devices for scale testing"""
    
    config_content = """poller:
  interval: 30  # Poll every 30 seconds
  timeout: 10   # SNMP timeout in seconds
  retries: 3    # Number of retries
  
  # ZeroMQ configuration for sending data to aggregator
  aggregator:
    address: "localhost"
    port: 5555

  # List of devices to poll
  devices:
"""
    
    for i in range(1, num_devices + 1):
        ip_address = f"{base_ip}.{start_ip + i - 1}"
        device_config = f"""    - hostname: "{ip_address}"
      community: "public"
      version: 2
      port: 161
"""
        config_content += device_config
    
    config_content += """

aggregator:
  # Database configuration
  database:
    path: "data/switchmap.db"
  
  # ZeroMQ configuration for receiving data from pollers
  zeromq:
    address: "*"
    port: 5555
  
  # Web server configuration (for future web interface)
  web:
    host: "localhost"
    port: 8080

# Logging configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
    
    with open("config/config_scale.yaml", 'w') as f:
        f.write(config_content)
    
    print(f"Generated config/config_scale.yaml with {num_devices} devices")

if __name__ == "__main__":
    # Generate configs for 20 devices
    generate_snmp_configs(20)
    generate_config_yaml(20)
    
    print("\nScale testing configs generated!")
    print("- 20 SNMP device configs in snmp-devices/")
    print("- config/config_scale.yaml with 20 devices")
    print("\nTo use the scale config:")
    print("1. Deploy containerlab: containerlab deploy -t linux-test.clab.yml")
    print("2. Copy config: cp config/config_scale.yaml config/config.yaml") 
    print("3. Run aggregator: python run_aggregator.py")
    print("4. Run poller: python run_poller.py") 