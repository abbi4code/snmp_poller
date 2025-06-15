# SNMP Poller Architecture

## Overview

The SNMP Poller is a distributed system designed for efficient collection and processing of SNMP data from network devices. It follows a modular architecture that separates concerns between data collection, processing, and storage.

## System Components

### 1. Poller Module
- **Purpose**: Handles SNMP data collection from network devices
- **Key Components**:
  - `async_snmp.py`: Asynchronous SNMP operations
  - `device.py`: Device management and configuration
  - `main.py`: Main polling logic and coordination

### 2. Aggregator Module
- **Purpose**: Processes and aggregates collected SNMP data
- **Key Components**:
  - `collector.py`: Data collection from pollers
  - `storage.py`: Data persistence and management
  - `__init__.py`: Aggregator initialization and coordination

### 3. Configuration Management
- **Location**: `config/` directory
- **Purpose**: Manages system configuration and device settings
- **Files**:
  - `config.yaml`: Main configuration file
  - `config_scale.yaml`: Configuration for scaled testing

### 4. Data Storage
- **Location**: `data/` directory
- **Purpose**: Stores collected metrics and system data
- **Format**: SQLite database (using aiosqlite)

## Communication Flow

1. **Device Discovery**:
   - System reads device configurations from YAML files
   - Establishes SNMP connections to target devices

2. **Data Collection**:
   - Poller module asynchronously collects SNMP data
   - Uses PySNMP for SNMP operations
   - Implements efficient polling strategies

3. **Data Processing**:
   - Aggregator receives data from pollers
   - Processes and normalizes the data
   - Stores results in the database

4. **Data Storage**:
   - Asynchronous database operations
   - Efficient data organization
   - Quick retrieval capabilities

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Network Infrastructure"
        D1["Device 1<br/>(SNMP Agent)"]
        D2["Device 2<br/>(SNMP Agent)"]
        D3["Device 3<br/>(SNMP Agent)"]
        DN["Device N<br/>(SNMP Agent)"]
    end
    
    subgraph "SNMP Poller System"
        subgraph "Poller Module"
            PM["main.py<br/>(Polling Logic)"]
            AS["async_snmp.py<br/>(Async SNMP Ops)"]
            DM["device.py<br/>(Device Management)"]
        end
        
        subgraph "Aggregator Module"
            AC["collector.py<br/>(Data Collection)"]
            AI["__init__.py<br/>(Coordination)"]
            ST["storage.py<br/>(Data Persistence)"]
        end
        
        subgraph "Configuration"
            CF1["config.yaml"]
            CF2["config_scale.yaml"]
        end
        
        subgraph "Data Storage"
            DB["SQLite Database<br/>(aiosqlite)"]
            DF["Data Files"]
        end
    end
    
    subgraph "Network Simulation"
        CL["ContainerLab"]
        SC["SNMP Configs"]
    end
    
    %% Data Flow Connections
    D1 -.->|"SNMP Requests"| AS
    D2 -.->|"SNMP Requests"| AS
    D3 -.->|"SNMP Requests"| AS
    DN -.->|"SNMP Requests"| AS
    
    AS -->|"Collected Data"| PM
    DM -->|"Device Info"| PM
    PM -->|"Processed Data"| AC
    
    AC -->|"Aggregated Data"| AI
    AI -->|"Store Data"| ST
    ST -->|"Write"| DB
    ST -->|"Write"| DF
    
    CF1 -->|"Config"| PM
    CF2 -->|"Scale Config"| PM
    CF1 -->|"Config"| AI
    
    CL -.->|"Creates"| D1
    CL -.->|"Creates"| D2
    CL -.->|"Creates"| D3
    CL -.->|"Creates"| DN
    SC -->|"SNMP Setup"| CL
    
    %% Process Flow
    PM <-->|"ZeroMQ"| AC
    
    style PM fill:#e1f5fe
    style AS fill:#e1f5fe
    style DM fill:#e1f5fe
    style AC fill:#f3e5f5
    style AI fill:#f3e5f5
    style ST fill:#f3e5f5
    style DB fill:#fff3e0
    style CF1 fill:#e8f5e8
    style CF2 fill:#e8f5e8
```


## Technical Stack

- **Language**: Python 3.8+
- **Key Dependencies**:
  - pysnmp (6.2.6): SNMP operations
  - pyyaml (6.0.1): Configuration management
  - pyzmq (25.1.2): Inter-process communication
  - aiosqlite (0.17.0): Asynchronous database operations

## Scalability Features

1. **Asynchronous Operations**:
   - Non-blocking SNMP operations
   - Efficient resource utilization
   - High concurrency support

2. **Modular Design**:
   - Independent components
   - Easy to extend and modify
   - Clear separation of concerns

3. **Configuration Flexibility**:
   - Dynamic device management
   - Adjustable polling parameters
   - Scalable testing configurations


## Future Enhancements

1. **Planned Features/Improvements**:
   - Stored polled data in the form of blob
   - Configured config to work for different zones
   - Implementation of CurveMQ and ZAP to authenticate the pollers with correct aggregator
   - Different polling interval for different matrices

