# 🖥️ PC UART Communication with Protobuf

## Overview
This Python application implements the **PC-side component** of a bidirectional communication system with an **ESP32 DevKit** over **UART**, using **Google Protocol Buffers (Protobuf)** for message serialization.

The program reads text input from the user, attaches a timestamp, serializes it with Protobuf, and transmits it to the ESP32 device through a selected serial port.

---

## 🧱 Features
- Interactive **command-line interface** (CLI)
- **Automatic timestamp** (milliseconds since epoch)
- **Protobuf-based serialization**
- **UART communication** using the `pyserial` library
- **Logging system** that records all key events to `log.txt`
- Managed by the **uv** package manager for reproducible environments

---

## 📂 Project Structure
```yaml
pc_uart_proto/
│
├── proto/
│ └── message.proto # Protobuf schema
│
├── pc_uart_proto/
│ ├── main.py # Entry point
│ ├── uart_utils.py # Serial port helpers
│ ├── protobuf_utils.py # Serialization helpers
│ ├── log_utils.py # Logging functions
│ └── init.py
│
├── log.txt # Runtime log file (ignored by .gitignore)
├── pyproject.toml # Project configuration (uv-managed)
├── uv.lock # uv lockfile (not necessary to track)
└── README.md # This documentation
```
---

## 🧰 Requirements

### System
- **OS:** Windows 11, macOS, or Linux  
- **Python:** ≥ 3.10  
- **UART adapter** connected to the ESP32

### Dependencies
Installed automatically when setting up with `uv`:
- `protobuf`
- `pyserial`

---

## ⚙️ Environment Setup

### 1. Install uv (if not installed)
```bash
pip install uv
```

### 2. Create environment and install dependencies
```bash
uv venv
uv sync
```

### 3. Activate environment
```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

## 🚀 Running the Program
1. Connect the **ESP32 DevKit** via USB.
2. Run the program directly with uv:
```bash
 uv run pc_uart_proto/main.py
```
3. Select the desired COM port (the program lists available ports).
4. Type any message and press Enter to send it.
5. To exit, press Ctrl + C or type an empty line.

## 🚀 Running the Program
1. Connect the ESP32 DevKit via USB.
2. Run the program:
```bash
python -m pc_uart_proto.main
```
3. Select the desired COM port (the program lists available ports).
4. Type any message and press Enter to send it.
5. To exit, press Ctrl + C or type an empty line.

## 🧾 Example Session
```vbnet
=====================================
Project name: pc_uart_proto
Author: Blaž Truden
Version: v1.0.0
=====================================
Available COM ports:
1. COM3
2. COM4
Select port: 1
✅ Connected to COM3
Type a message to send (Enter to send, empty line to exit):
> Hello ESP32!
📤 Sent 23 bytes over UART
```

## 🧩 Protobuf Schema (message.proto)
```proto
syntax = "proto3";

message UartMessage {
  uint64 timestamp = 1; // milliseconds since epoch
  string data = 2;      // UTF-8 encoded message
}
```

## 📚 Design Notes
- Protobuf ensures compact and well-defined message structures, easily extendable to include ACKs or future fields.
- The timestamp field is included on the PC side for traceability.
- A logging mechanism writes events to log.txt for debugging and analysis.
- UART frame format:
Each Protobuf message is preceded by a 4-byte length header (little-endian), allowing the ESP32 to parse message boundaries reliably.

## ⚠️ Error Handling
- Invalid COM port selections cause the program to reprompt the user.
- UART write/read exceptions are caught and logged.
- The program safely closes the serial connection upon exit or error.