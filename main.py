"""
PC ↔ ESP32 UART Communication
==============================

This script provides a command-line interface for connecting to an ESP32
development board over a serial (UART) connection.  The user can select
an available COM port, open the connection, and (later) send or receive
data.  The design emphasizes clarity and modularity so that additional
features—such as Protobuf serialization—can be added easily.

Author: Blaž Truden
Date: 2025-10-04
"""

import serial
import serial.tools.list_ports

# === Configuration constants ===
BAUDRATE = 115200          # Default UART speed (bits per second)
TIMEOUT = 1.0              # Serial read timeout (seconds)


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


def main():
    """
    Entry point for the PC-side UART communication program.

    Handles user interaction for selecting and opening a COM port.
    Future extensions will add functions for sending/receiving data
    serialized with Protobuf.
    """
    print("=== PC ↔ ESP32 UART Communication ===")

    selected_port = select_port()
    if selected_port is None:
        print("Exiting program.")
        return

    ser = open_serial_connection(selected_port)
    if ser is None:
        return

    # Placeholder for next steps (sending/receiving data)
    ser.close()
    print("🔌 Connection closed.")


if __name__ == "__main__":
    main()
