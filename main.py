import serial
import serial.tools.list_ports


def list_available_ports():
    """Return a list of available COM ports."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def select_port():
    """Display available ports and allow the user to select or refresh."""
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
            continue  # refresh list
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(ports):
                    return ports[idx - 1]
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")


def open_serial_connection(port, baudrate=115200, timeout=1):
    """Open and return a serial connection."""
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        print(f"\n✅ Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"\n❌ Failed to open port {port}: {e}")
        return None


def main():
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
