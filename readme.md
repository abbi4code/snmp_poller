## Setting ContainerLab for testing 
- Set up Alpine Linux containers with SNMP tools
  
#OS - Linux 

### Install ContainerLab
`bash -c "$(curl -sL https://get.containerlab.dev)"`

### Output
![Screenshot from 2025-06-10 15-23-03](https://github.com/user-attachments/assets/df4d26bd-fa2e-41fa-84f2-a75c2b79dd5b)

### Add yourself to container admin group
`sudo usermod -aG clab_admins abhishek`

### Configure your containerLab setup for SNMP daemons 
- eg- 
``
name: linux-test

topology:
  nodes:
    switch01:
      kind: linux
      image: alpine:latest
      binds:
        - snmp-devices:/shared:ro
      exec:
        - apk add --no-cache net-snmp net-snmp-tools
        - mkdir -p /etc/snmp
        - cp /shared/snmpd-1.conf /etc/snmp/snmpd.conf
        - snmpd -f -Lo &
  links: []

mgmt:
  network: clab-mgmt
  ipv4-subnet: 172.20.20.0/24
``

### Generate Config files for your daemons

- Run `generate_snmp_configs.py`

### Deploy 20-device topology
`sudo containerlab deploy -t linux-test.clab.yml`

### Use scale config
`cp config/config_scale.yaml config/config.yaml`

### Run aggregator & poller in seperate terminal 

First activate your virtual env
- `source venv/bin/activate`

#### Terminal 1
- `python aggregator/__init_.py`

#### Terminal 2
- `python run_poller.py`

#### Outputs on poller side
  ![Screenshot from 2025-06-10 17-00-05](https://github.com/user-attachments/assets/277f6555-66fd-4337-9c64-f61e19defc7d)

![Screenshot from 2025-06-10 17-01-05](https://github.com/user-attachments/assets/aa847f22-eb79-43a1-9318-52e75ee73d5c)

#### Outputs on aggregator side

![Screenshot from 2025-06-10 17-02-02](https://github.com/user-attachments/assets/0c8e314e-55eb-44b7-b216-4f0a186bfe92)
