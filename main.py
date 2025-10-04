"""
PC ↔ ESP32 UART Communication
==============================

This script provides a command-line interface for connecting to an ESP32
development board over a serial (UART) connection. The user can select
an available COM port, open the connection, and send text data entered
from the keyboard. Each message is framed according to the format:

    [SOF][length 2 bytes][payload][CRC16][EOF]

The design is modular to simplify future expansion (such as adding
Protobuf serialization or timestamping).

Author: Blaž Truden
Date: 2025-10-04
"""

import struct
import serial
import serial.tools.list_ports
from datetime import datetime

# === Configuration constants ===
BAUDRATE = 115200            # Default UART speed (bits per second)
TIMEOUT = 1.0                # Serial read timeout (seconds)
MAX_MESSAGE_LENGTH = 128     # Maximum allowed message length in bytes

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

    The function calculates the payload length, encodes it in big-endian
    format, computes a CRC16 checksum over the payload, and returns
    the full framed byte sequence.

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
        list[str]: A list of port device names, for example:
                   ["COM3", "COM5"] on Windows or
                   ["/dev/ttyUSB0", "/dev/ttyACM0"] on Linux/macOS.
    """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def select_port():
    """
    Display the list of available COM ports and prompt the user to select one.

    The user can:
        • Enter a port number to select it.
        • Enter '0' to refresh the list of detected ports.
        • Enter 'q' to quit the program.

    Returns:
        str | None: The selected port name (e.g., "COM3"), or None if
        the user chose to quit.
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
            continue  # Refresh list and start loop again
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
        serial.Serial | None: An open serial connection object if successful,
        or None if the connection attempt failed.
    """
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        print(f"\n✅ Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"\n❌ Failed to open port {port}: {e}")
        return None


def transmit_user_input(ser):
    """
    Continuously read lines from the user and send them over UART.

    The user can type any text and press Enter to transmit it to the ESP32.
    Typing 'exit' (case-insensitive) closes the session and returns.

    Each message is:
        - limited to MAX_MESSAGE_LENGTH bytes,
        - framed as [SOF][length][payload][CRC16][EOF].

    Args:
        ser (serial.Serial): An open serial connection.
    """
    print("\n=== UART Transmission Mode ===")
    print(f"Type messages to send (max {MAX_MESSAGE_LENGTH} bytes). Type 'exit' to quit.\n")

    try:
        while True:
            user_input = input("> ").strip()
            if user_input.lower() == "exit":
                print("Exiting transmission mode...")
                break

            # Encode and validate payload length
            encoded = user_input.encode("utf-8")
            if len(encoded) > MAX_MESSAGE_LENGTH:
                print(f"⚠️ Message too long ({len(encoded)} bytes). Limit is {MAX_MESSAGE_LENGTH} bytes.")
                continue

            # Frame and send the message
            framed = frame_message(encoded)
            ser.write(framed)
            print(f"📤 Sent {len(framed)} bytes.")

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting transmission mode.")
    except serial.SerialException as e:
        print(f"\n⚠️ Serial error: {e}")


def main():
    """
    Entry point for the PC-side UART communication program.

    Displays program metadata including the current date and time.
    Handles user interaction for selecting and opening a COM port.
    Once connected, the user can transmit messages interactively
    until typing 'exit' or closing the connection.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=====================================")
    print("Project name: pc_uart_proto")
    print("Author: Blaž Truden")
    print("Date: 2025-10-04")
    print(f"Launch time: {now}")
    print("=====================================")

    selected_port = select_port()
    if selected_port is None:
        print("Exiting program.")
        return

    ser = open_serial_connection(selected_port)
    if ser is None:
        return

    transmit_user_input(ser)

    ser.close()
    print("🔌 Connection closed.")


if __name__ == "__main__":
    main()
