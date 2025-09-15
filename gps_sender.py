import serial
import time
import requests

SERIAL_PORT = "COM3"          # Replace with your port
BAUD_RATE = 115200
URL = "https://your-render-url/rover"  # Your Flask server
ROVER_ID = "rover1"

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

while True:
    try:
        # Request location from module
        ser.write(b'AT+QGPSLOC=2\r')
        time.sleep(2)

        line = ser.readline().decode(errors="ignore").strip()
        if "+QGPSLOC:" in line:
            data = line.split(":")[1].split(",")
            lat = data[1]
            lon = data[2]

            payload = {
                "id": ROVER_ID,
                "gps": {"latitude": lat, "longitude": lon},
                "heartbeat": 1
            }

            try:
                r = requests.post(URL, json=payload)
                print(f"Sent: {payload}, Server response: {r.status_code}")
            except Exception as e:
                print("Error sending to server:", e)

        time.sleep(30)  # send every 30 seconds

    except Exception as e:
        print("Serial read error:", e)
        time.sleep(5)
