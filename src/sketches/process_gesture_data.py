"""
Process Gesture Data - Serial to CSV Converter (Improved)

This script reads accelerometer data from the ESP32 serial port and 
automatically saves it to CSV files. It supports dynamic gesture name input,
so you can collect multiple gesture classes in one session.

Usage:
    python process_gesture_data.py [options]

Options:
    --port PORT       Serial port to use (default: auto-detect)
    --baud BAUD       Baud rate (default: 115200)
    --person NAME     Person name (default: "user")
    --output DIR      Output directory (default: "data")
"""

import serial
import serial.tools.list_ports
import os
import time
import argparse
import csv
from datetime import datetime
import sys

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "CP210" in p.description or "CH340" in p.description or "FTDI" in p.description or "USB Serial" in p.description:
            return p.device
    return None

def list_available_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return "No serial ports found."
    
    result = "Available ports:\n"
    for i, p in enumerate(ports):
        result += f"{i+1}. {p.device} - {p.description}\n"
    return result

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def save_data_to_csv(filepath, data):
    timestamps = [i * 10 for i in range(len(data))]
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'x', 'y', 'z'])
        for i, (x, y, z) in enumerate(data):
            writer.writerow([timestamps[i], x, y, z])
    print(f"Saved {len(data)} samples to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Process gesture data from ESP32")
    parser.add_argument("--port", help="Serial port to use (default: auto-detect)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--person", default="user", help="Person name (default: 'user')")
    parser.add_argument("--output", default="data", help="Output directory (default: 'data')")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    args = parser.parse_args()
    
    if args.list_ports:
        print(list_available_ports())
        return

    port = args.port
    if not port:
        port = find_arduino_port()
        if not port:
            print("Error: Could not auto-detect ESP32 port.")
            print(list_available_ports())
            print("Please specify with --port or try --list-ports to see available options.")
            return

    print(f"Connecting to ESP32 on {port} at {args.baud} baud...")

    try:
        ser = serial.Serial(port, args.baud, timeout=1)
        time.sleep(2)
        
        print("Connected! Waiting for gesture data...")
        print("Press Ctrl+C to exit at any time.")
        
        capture_count = 0

        while True:
            # Prompt user for the gesture name
            gesture = input("\nEnter gesture name (or type 'exit' to quit): ").strip()
            if gesture.lower() == 'exit':
                print("Exiting session...")
                break

            # Make sure the output directory for this gesture exists
            gesture_dir = os.path.join(args.output, gesture)
            ensure_directory(gesture_dir)

            print(f"Ready to capture gesture '{gesture}'.")
            print("Type 'o' to start capture (will automatically stop after 1 second).")

            collecting = False
            current_data = []

            while True:
                if ser.in_waiting:
                    try:
                        line = ser.readline().decode('utf-8').strip()

                        if "-,-,-" in line:
                            collecting = True
                            current_data = []
                            print("Capture started...")
                            continue

                        if "Capture complete" in line:
                            if current_data:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                capture_count += 1
                                filename = f"output_{gesture}_{args.person}_{capture_count}_{timestamp}.csv"
                                filepath = os.path.join(gesture_dir, filename)
                                save_data_to_csv(filepath, current_data)
                            else:
                                print("Warning: No data was collected.")
                            collecting = False
                            print(f"Capture for gesture '{gesture}' complete.\n")
                            break  # Exit the inner loop, go back to gesture selection

                        if collecting:
                            if "," in line:
                                try:
                                    x, y, z = map(float, line.split(','))
                                    current_data.append([x, y, z])
                                except ValueError:
                                    pass
                    except UnicodeDecodeError:
                        pass

                # Handle user key press to trigger capture
                if os.name == 'nt':
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8')
                        if key == 'o':
                            ser.write(b'o')
                            print("Sent start command...")
                else:
                    import sys, select
                    if select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key == 'o':
                            ser.write(b'o')
                            print("Sent start command...")

                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nExiting session (Ctrl+C pressed).")
    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    try:
        import serial
    except ImportError:
        print("Error: The 'pyserial' module is not installed.")
        print("Please install it with: pip install pyserial")
        sys.exit(1)

    main()
    