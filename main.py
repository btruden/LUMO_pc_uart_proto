"""
PC ↔ ESP32 UART Communication
==============================

This script provides a command-line interface for connecting to an ESP32
development board over a serial (UART) connection. The user can select
an available COM port, open the connection, and send text data entered
from the keyboard. The design is modular to simplify future expansion
(such as adding Protobuf serialization or timestamping).

Author: Blaž Truden
Date: 2025-10-04
"""

import serial
import serial.tools.list_ports

# === Configuration constants ===
BAUDRATE = 115200           # Default UART speed (bits per second)
TIMEOUT = 1.0               # Serial read timeout (seconds)
MAX_MESSAGE_LENGTH = 128    # Maximum allowed message length in bytes


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

    Message length is limited to MAX_MESSAGE_LENGTH bytes. If the user
    enters a longer message, it will be rejected with a warning.

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

            # Check message length
            encoded = user_input.encode("utf-8")
            if len(encoded) > MAX_MESSAGE_LENGTH:
                print(f"⚠️ Message too long ({len(encoded)} bytes). Limit is {MAX_MESSAGE_LENGTH} bytes.")
                continue

            # Convert to bytes and send
            ser.write(encoded)
            ser.write(b"\n")  # optional newline
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting transmission mode.")
    except serial.SerialException as e:
        print(f"\n⚠️ Serial error: {e}")


def main():
    """
    Entry point for the PC-side UART communication program.

    Handles user interaction for selecting and opening a COM port.
    Once connected, the user can transmit messages interactively
    until typing 'exit' or closing the connection.
    """
    print("=====================================")
    print("Project name: pc_uart_proto")
    print("Author: Blaž Truden")
    print("Date: 2025-10-04")
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
