# SNMP Poller

A scalable SNMP polling system that efficiently collects and aggregates network device data.

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- ContainerLab (for network simulation)
- Docker (for running containers)

### Step 1: Set Up Your Environment

1. Clone this repository:
```bash
git clone https://github.com/abbi4code/snmp_poller.git
cd snmp_poller
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Network Simulation

1. Install ContainerLab:
```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

2. Add yourself to the container admin group:
```bash
sudo usermod -aG clab_admins $USER
```

3. Generate SNMP configuration files:
```bash
python scripts/generate_snmp_configs.py
```

4. Deploy the test network topology:
```bash
sudo containerlab deploy -t linux-test.clab.yml
```

### Step 3: Run the Application

1. Start the aggregator (in one terminal):
```bash
source venv/bin/activate
python aggregator/__init__.py
```

2. Start the poller (in another terminal):
```bash
source venv/bin/activate
python run_poller.py
```

## Configuration

- The default configuration is in `config/config.yaml`
- For testing with more devices, use the scale configuration:
```bash
cp config/config_scale.yaml config/config.yaml
```

## Monitoring

- The poller will show real-time SNMP polling results
- The aggregator will display collected and processed data
- Check the `data/` directory for stored metrics
- Like you can do this 
```bash
sqlite3 ./data/devices.db
.tables
select * from devices/interfaces # jst an example
```

## Troubleshooting

1. If you encounter permission issues with ContainerLab:
   - Ensure you're in the `clab_admins` group
   - Try logging out and back in after adding the group

2. If SNMP polling fails:
   - Verify the network topology is running (`sudo containerlab inspect -t linux-test.clab.yml`)
   - Check SNMP configurations in `snmp-devices/`

## Additional Resources

- [SNMP Documentation](https://www.ietf.org/rfc/rfc1157.txt)
- [ContainerLab Documentation](https://containerlab.dev/)
- [PySNMP Documentation](https://pysnmp.readthedocs.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request 😎.
