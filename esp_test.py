# pc_uart_proto_test_menu.py
"""
PC ↔ ESP32 UART Communication — Test Menu Edition

This script is based on the user's original main.py and adds a test menu
that sends malformed frames to the ESP32 for debugging.

Uses same framing:
    [SOF][length 2 bytes][payload][CRC16][EOF]

Author: adapted for tests by ChatGPT (for Blas Truden)
Based on original script: main.py. :contentReference[oaicite:1]{index=1}
"""

import struct
import serial
import serial.tools.list_ports
from datetime import datetime
from time import time
from random import randint
from uart_proto import uart_pb2  # generated protobuf (same as your original)
from logger_util import log_message

# === Configuration constants ===
BAUDRATE = 115200
TIMEOUT = 1.0
MAX_MESSAGE_LENGTH = 128  # used for normal mode; tests can exceed if needed

# Frame bytes
SOF = b'\x02'
EOF = b'\x03'


def crc16_ibm(data: bytes) -> int:
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
    """Normal/valid framed message."""
    length_bytes = struct.pack(">H", len(payload))
    crc_bytes = struct.pack(">H", crc16_ibm(payload))
    return SOF + length_bytes + payload + crc_bytes + EOF


# ---------- Malformed frame builders (tests) ----------
def frame_missing_sof(payload: bytes) -> bytes:
    """Drop SOF, send rest normally."""
    length_bytes = struct.pack(">H", len(payload))
    crc_bytes = struct.pack(">H", crc16_ibm(payload))
    return length_bytes + payload + crc_bytes + EOF


def frame_missing_eof(payload: bytes) -> bytes:
    """Drop EOF, send rest normally."""
    length_bytes = struct.pack(">H", len(payload))
    crc_bytes = struct.pack(">H", crc16_ibm(payload))
    return SOF + length_bytes + payload + crc_bytes


def frame_wrong_length_field(payload: bytes) -> bytes:
    """Corrupt length field (set to real length ± random delta)."""
    # introduce a random delta between -3 and +7 but keep unsigned 16-bit
    delta = randint(-3, 7)
    fake_len = (len(payload) + delta) & 0xFFFF
    length_bytes = struct.pack(">H", fake_len)
    crc_bytes = struct.pack(">H", crc16_ibm(payload))
    return SOF + length_bytes + payload + crc_bytes + EOF


def frame_wrong_crc(payload: bytes) -> bytes:
    """Corrupt CRC bytes (flip some bits)."""
    length_bytes = struct.pack(">H", len(payload))
    good_crc = crc16_ibm(payload)
    # flip some bits to make CRC wrong
    bad_crc = good_crc ^ 0xA5A5
    crc_bytes = struct.pack(">H", bad_crc & 0xFFFF)
    return SOF + length_bytes + payload + crc_bytes + EOF


def frame_payload_length_mismatch(payload: bytes) -> bytes:
    """
    Make the length field different from actual payload length.
    For example: length set to len(payload) + 5 but only send original payload.
    """
    fake_len = (len(payload) + 5) & 0xFFFF
    length_bytes = struct.pack(">H", fake_len)
    crc_bytes = struct.pack(">H", crc16_ibm(payload))
    return SOF + length_bytes + payload + crc_bytes + EOF


def frame_payload_too_high(payload: bytes = None, target_length: int = 600) -> bytes:
    """
    Build a frame with a very large payload (e.g., 600 bytes).
    If a payload is provided it will be repeated or padded to reach target_length.
    Otherwise filler bytes are used.
    """
    if payload:
        # repeat the serialized payload until we reach or exceed target_length, then cut
        rep = (target_length + len(payload) - 1) // len(payload)
        big_payload = (payload * rep)[:target_length]
    else:
        big_payload = b'A' * target_length

    length_bytes = struct.pack(">H", len(big_payload))
    crc_bytes = struct.pack(">H", crc16_ibm(big_payload))
    return SOF + length_bytes + big_payload + crc_bytes + EOF


# ---------- Utilities ----------
def list_available_ports():
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def select_port():
    while True:
        ports = list_available_ports()
        log_message(f"Detected {len(ports)} COM port(s): {ports}")
        print("\n=== Available COM ports ===")
        if not ports:
            print("  (none detected)")
        else:
            for i, port in enumerate(ports, start=1):
                print(f"  {i}. {port}")
        print("\n  0. 🔄 Refresh list\n  q. ❌ Quit")
        choice = input("\nSelect a port number: ").strip().lower()
        if choice == "q":
            log_message("User quit port selection.")
            return None
        if choice == "0":
            continue
        try:
            idx = int(choice)
            if 1 <= idx <= len(ports):
                log_message(f"User selected port: {ports[idx-1]}")
                return ports[idx-1]
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def open_serial_connection(port, baudrate=BAUDRATE, timeout=TIMEOUT):
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        print(f"\n✅ Connected to {port} at {baudrate} baud.")
        log_message(f"Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"\n❌ Failed to open port {port}: {e}")
        log_message(f"Failed to open port {port}: {e}")
        return None


def build_data_message(text: str) -> bytes:
    msg = uart_pb2.UartMessage()
    msg.data_message.timestamp = int(time() * 1000)
    msg.data_message.data = text
    log_message(f"Built DataMessage for test payload length={len(msg.SerializeToString())}")
    return msg.SerializeToString()


def send_and_report(ser, framed: bytes, note: str = ""):
    try:
        ser.write(framed)
        print(f"Sent {len(framed)} bytes. {note}")
        log_message(f"Sent test frame: {note} ({len(framed)} bytes)")
    except serial.SerialException as e:
        print(f"Serial write error: {e}")
        log_message(f"Serial write error: {e}")


# ---------- Test menu ----------
def test_menu(ser):
    """
    Interactive menu for sending malformed frames.
    Each test sends one frame by default; user can repeat as needed.
    """
    menu = """
=== UART Test Menu ===
1) SOF missing
2) EOF missing
3) Wrong length field
4) Wrong CRC
5) Payload length different from length field
6) Payload length too high (~600 bytes)
r) Send a VALID (control) message
q) Quit test menu
Enter choice: """
    while True:
        choice = input(menu).strip().lower()
        if choice == "q":
            log_message("Exiting test menu.")
            break
        if choice == "r":
            text = input("Enter text to send in a VALID frame (or enter for default): ").strip()
            if not text:
                text = f"control-{int(time()*1000)}"
            payload = build_data_message(text)
            framed = frame_message(payload)
            send_and_report(ser, framed, "VALID frame")
            continue

        if choice not in {"1", "2", "3", "4", "5", "6"}:
            print("Invalid choice.")
            continue

        # Use a short default text payload for tests to make interpretation easier on ESP
        default_text = f"test_{choice}_{int(time()*1000)}"
        base_payload = build_data_message(default_text)

        if choice == "1":
            framed = frame_missing_sof(base_payload)
            note = "SOF missing"
        elif choice == "2":
            framed = frame_missing_eof(base_payload)
            note = "EOF missing"
        elif choice == "3":
            framed = frame_wrong_length_field(base_payload)
            note = "wrong length field"
        elif choice == "4":
            framed = frame_wrong_crc(base_payload)
            note = "wrong CRC"
        elif choice == "5":
            framed = frame_payload_length_mismatch(base_payload)
            note = "payload length mismatch"
        elif choice == "6":
            # For test 6, prompt whether to craft with the protobuf repeated or filler
            sub = input("Use repeated protobuf (r) or filler (f)? [f]: ").strip().lower()
            if sub == "r":
                framed = frame_payload_too_high(base_payload, target_length=600)
            else:
                framed = frame_payload_too_high(None, target_length=600)
            note = "payload too high (600 bytes)"

        send_and_report(ser, framed, note)

        # Optionally allow repeated sends
        rep = input("Send same test again? (y/N): ").strip().lower()
        if rep == "y":
            try:
                send_and_report(ser, framed, note + " (repeat)")
            except Exception:
                pass


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=====================================")
    print("Project name: pc_uart_proto (test menu)")
    print("Author: Blaž Truden (adapted)")
    print(f"Date: {now}")
    print("=====================================")
    log_message("Test program started.")

    ser = None
    while ser is None:
        selected_port = select_port()
        if selected_port is None:
            print("Exiting program.")
            log_message("Program terminated by user.")
            return
        ser = open_serial_connection(selected_port)
        if ser is None:
            print("\n⚠️ Could not open port. Try a different port.")
            log_message("Retrying port selection after failure.")
            continue

    # Open the test menu after connecting
    test_menu(ser)

    ser.close()
    print("🔌 Connection closed.")
    log_message("Program terminated.")


if __name__ == "__main__":
    main()
