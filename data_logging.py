import serial      
import csv        
import os         
import time      
from datetime import datetime 

SERIAL_PORT = '/dev/tty.usbmodem1101' # Which COM/serial port the board is connected to (I used both mac and windows so this changed on each)
BAUD_RATE = 9600              
SESSION_LABEL = 'Demo' # Changing session name depending what session we are capturing
OUTPUT_FILE = f'{SESSION_LABEL}_raw.csv' # Builds the output filename from the session label

# Don't overwrite an existing session file in case
if os.path.exists(OUTPUT_FILE): # Guards against accidentally overwriting old data
    raise FileExistsError(
        f"{OUTPUT_FILE} already exists — rename SESSION_LABEL or move the old file before rerunning"
    )

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)  # Opens the serial connection to the Arduino
time.sleep(2) # Lets the board finish its reset before we start reading
ser.reset_input_buffer() # Discards anything that may be sitting in the buffer

with open(OUTPUT_FILE, 'w', newline='') as f: # Open the CSV file for writing
    writer = csv.writer(f) # Create a CSV writer object
    writer.writerow(['timestamp', 'session', 'soil_raw', 'lux', 'temp_c', 'humidity_pct'])

    print(f"Logging to {OUTPUT_FILE} — press Ctrl+C to stop")
    try:
        while True: # Keep reading until interrupted
            try:
                line = ser.readline().decode(errors='ignore').strip() # Read one line from serial, decode to text
            except serial.SerialException as e:
                print(f"Serial error: {e} — check the connection") # Board disconnected or port error
                break # Stop the loop

            if not line or "Soil:" not in line: # Skip any empty lines or lines that aren't sensor readings
                continue
            try:
                # Strip labels so only raw values are left
                parts = line.replace("Soil: ", "").replace("Lux: ", "").replace("Temp: ", "").replace("C", "").replace("Humidity: ", "").replace("%", "")
                soil, lux, temp, hum = [p.strip() for p in parts.split("|")]  # Split into the 4 values
                timestamp = datetime.now().isoformat() # Record timestamp
                writer.writerow([timestamp, SESSION_LABEL, soil, lux, temp, hum])  # Write the row to CSV
                f.flush() # Force write to disk immediately so we don't lose data on crash
                print(timestamp, soil, lux, temp, hum) # Echoes the reading to the console
            except ValueError:
                continue  # Skips malformed lines
    except KeyboardInterrupt:
        print("Logging stopped.")  
    finally:
        ser.close()   # Close serial port