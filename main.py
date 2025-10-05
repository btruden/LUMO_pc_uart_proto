"""
PC ↔ ESP32 UART Communication
==============================

This script provides a command-line interface for connecting to an ESP32
development board over a serial (UART) connection. The user can select
an available COM port, open the connection, and send text data entered
from the keyboard. Each message is serialized using Protobuf and then
framed according to the format:

    [SOF][length 2 bytes][payload][CRC16][EOF]

The design is modular to simplify future expansion and mirrors the same
Protobuf schema used on the ESP32 side.

Author: Blaž Truden
Date: 2025-10-04
"""

import struct
import serial
import serial.tools.list_ports
from datetime import datetime
from time import time
from uart_proto import uart_pb2  # Generated from uart.proto
from logger_util import log_message

# === Configuration constants ===
BAUDRATE = 115200            # Default UART speed (bits per second)
TIMEOUT = 1.0                # Serial read timeout (seconds)
MAX_MESSAGE_LENGTH = 128     # Maximum allowed message length (before framing)

# === Frame format configuration ===
SOF = b'\x02'                # Start of Frame (default: STX 0x02)
EOF = b'\x03'                # End of Frame (default: ETX 0x03)


def crc16_ibm(data: bytes) -> int:
    """
    Compute a CRC-16/IBM checksum over the given data buffer.

    Polynomial: 0xA001 (reflected 0x8005)
    Initial value: 0xFFFF

    Args:
        data (bytes): Input data buffer.

    Returns:
        int: 16-bit CRC value.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def frame_message(payload: bytes) -> bytes:
    """
    Construct a framed message according to the format:
        [SOF][length (2 bytes)][payload][CRC16][EOF]

    Args:
        payload (bytes): The message payload to frame.

    Returns:
        bytes: The complete framed message ready for UART transmission.
    """
    length = len(payload)
    length_bytes = struct.pack(">H", length)  # 2 bytes, big-endian
    crc = crc16_ibm(payload)
    crc_bytes = struct.pack(">H", crc)
    return SOF + length_bytes + payload + crc_bytes + EOF


def list_available_ports():
    """
    Detect and return the list of available COM ports on the host system.

    Returns:
        list[str]: A list of port device names, e.g. ["COM3", "COM5"].
    """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def select_port():
    """
    Display the list of available COM ports and prompt the user to select one.

    The user can:
        • Enter a port number to select it.
        • Enter '0' to refresh the list.
        • Enter 'q' to quit.

    Returns:
        str | None: The selected port name, or None if the user quit.
    """
    while True:
        ports = list_available_ports()
        print("\n=== Available COM ports ===")
        if not ports:
            print("  (none detected)")
        else:
            for i, port in enumerate(ports, start=1):
                print(f"  {i}. {port}")

        print("")
        print("  0. 🔄 Refresh list")
        print("  q. ❌ Quit")

        choice = input("\nSelect a port number: ").strip().lower()

        if choice == "q":
            return None
        elif choice == "0":
            continue  # Refresh list and restart loop
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(ports):
                    return ports[idx - 1]
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")


def open_serial_connection(port, baudrate=BAUDRATE, timeout=TIMEOUT):
    """
    Attempt to open a serial connection to the specified port.

    Args:
        port (str): The name of the serial port (e.g., "COM3").
        baudrate (int): UART baud rate in bits per second.
        timeout (float): Read timeout in seconds.

    Returns:
        serial.Serial | None: An open serial connection if successful,
        or None if the attempt failed.
    """
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        print(f"\n✅ Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"\n❌ Failed to open port {port}: {e}")
        return None


def build_data_message(text: str) -> bytes:
    """
    Create a serialized Protobuf DataMessage with a timestamp and text.

    Args:
        text (str): The UTF-8 string payload entered by the user.

    Returns:
        bytes: Serialized Protobuf message.
    """
    msg = uart_pb2.UartMessage()
    msg.data_message.timestamp = int(time() * 1000)  # milliseconds since epoch
    msg.data_message.data = text
    return msg.SerializeToString()


def transmit_user_input(ser):
    """
    Continuously read lines from the user and send them over UART.

    Each line is:
        - Serialized into a Protobuf DataMessage
        - Framed as [SOF][length][payload][CRC16][EOF]
        - Sent through the open serial port

    Args:
        ser (serial.Serial): An open serial connection.
    """
    print("\n=== UART Transmission Mode ===")
    print(f"Type messages to send. Type 'exit' to quit.\n")

    try:
        while True:
            user_input = input("> ").strip()
            if user_input.lower() == "exit":
                print("Exiting transmission mode...")
                break

            # Serialize user input into Protobuf message
            serialized = build_data_message(user_input)

            if len(serialized) > MAX_MESSAGE_LENGTH:
                print(f"⚠️ Protobuf message too long ({len(serialized)} bytes). Limit is {MAX_MESSAGE_LENGTH} bytes.")
                continue

            # Frame and send
            framed = frame_message(serialized)
            ser.write(framed)
            print(f"📤 Sent {len(framed)} bytes (Protobuf payload size: {len(serialized)}).")

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting transmission mode.")
    except serial.SerialException as e:
        print(f"\n⚠️ Serial error: {e}")


def main():
    """
    Entry point for the PC-side UART communication program.

    Displays program metadata including the current date and time.
    Handles COM port selection, connection, and user message transmission.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=====================================")
    print("Project name: pc_uart_proto")
    print("Author: Blaž Truden")
    print("Version: v1.0.0")    # to be improved
    print("=====================================")

    log_message("Program started.")

    selected_port = select_port()
    if selected_port is None:
        print("Exiting program.")
        log_message("Program terminated.")
        return

    ser = open_serial_connection(selected_port)
    if ser is None:
        log_message("Program terminated.")
        return

    transmit_user_input(ser)

    ser.close()
    print("🔌 Connection closed.")
    log_message("Program terminated.")


if __name__ == "__main__":
    main()
