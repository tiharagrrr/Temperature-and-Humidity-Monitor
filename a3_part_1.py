"""
BME280 Sensor Reading Script
Student: Piyumi Tihara Egodage
ID: w1953194
Purpose: Read temperature, humidity, and pressure from BME280 sensor
"""

from time import localtime, sleep

import BME280
import network
import ntptime
from machine import I2C, Pin

# config constants
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0
I2C_FREQ = 40000
MEASUREMENT_DELAY = 5  # seconds

# WiFi Credentials
WIFI_SSID = "Teow"
WIFI_PASSWORD = "meowww96"

# Alternative WiFi
WIFI_SSID_BACKUP = "ez WiFi"
WIFI_PASSWORD_BACKUP = "basicpassword123"

# NTP Configuration
NTP_SERVER = "pool.ntp.org"  # NTP server to use
TIMEZONE_OFFSET = 5.5  # UTC offset in hours (0 for UK GMT, 1 for BST)


# Handles sensor readings
class SensorReader:
    # Initialize I2C and BME280 sensor
    def __init__(self):
        try:
            self.i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

            devices = self.i2c.scan()
            if not devices:
                raise Exception("No I2C devices found, re-check wiring.")

            print(f"I2C devices found at addresses: {[hex(d) for d in devices]}")

            # Initialize BME280
            self.bme = BME280.BME280(i2c=self.i2c)
            print("BME280 sensor initialized successfully!")

        except Exception as e:
            print(f"Sensor initialization error: {e}")
            raise

    def read_sensor(self):
        """
        Read all sensor values with error handling
        Returns: tuple (temperature, pressure, humidity) or None on error
        """
        try:
            temp_str, press_str, hum_str = self.bme.values

            # Parse values (remove units)
            temperature = float(temp_str.replace("C", ""))
            pressure = float(press_str.replace("hPa", ""))
            humidity = float(hum_str.replace("%", ""))

            return temperature, pressure, humidity

        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None

    def validate_reading(self, temp, press, hum):
        """
        Validate sensor readings are within physical limits, returns True if Valid
        """
        if not (-40 <= temp <= 85):
            print(f"Warning: Temperature {temp}°C is out of range")
            return False
        if not (300 <= press <= 1100):
            print(f"Warning: Pressure {press} hPa is out of range")
            return False
        if not (0 <= hum <= 100):
            print(f"Warning: Humidity {temp}% is out of range")
            return False

    def display_reading(self, reading_num):
        """Display a single reading with all calculations"""
        data = self.read_sensor()

        if data is None:
            print(f"Reading #{reading_num}: FAILED")
            return None

        temp, press, hum = data

        # Validate
        if not self.validate_reading(temp, press, hum):
            print(f"Reading #{reading_num}: INVALID DATA")
            return None

        # Get current timestamp
        current_time = localtime()
        displayTime = f"{current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d} {current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"

        # Display formatted output
        print("=" * 50)
        print(f"Reading #{reading_num} at time {displayTime}")
        print("=" * 50)
        print(f"Temperature:    {temp:.2f} °C")
        print(f"Pressure:       {press:.2f} hPa")
        print(f"Humidity:       {hum:.2f} %")
        print("=" * 50)

        return {"temperature": temp, "pressure": press, "humidity": hum}


def main():
    print("\n" + "=" * 50)
    print("BME280 SENSOR TEST - PART A3")
    print("=" * 50 + "\n")

    # Connect to WiFi for NTP sync
    print("Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        print(".", end="")
        sleep(0.5)

    print(f"\nConnected! IP: {wlan.ifconfig()[0]}")

    # Sync time with NTP server
    print(f"Synchronizing time with NTP server: {NTP_SERVER}")
    try:
        ntptime.host = NTP_SERVER  # Set NTP server explicitly
        ntptime.settime()  # Perform NTP synchronization
        current = localtime()
        print(
            f"✓ Time synced: {current[0]}-{current[1]:02d}-{current[2]:02d} {current[3]:02d}:{current[4]:02d}:{current[5]:02d} UTC"
        )
        print(f"✓ Timezone offset: UTC{TIMEZONE_OFFSET:+d}\n")
    except Exception as e:
        print(f"✗ NTP sync failed: {e}")
        print("⚠ Continuing with system time\n")

    # Initialize sensor
    sensor = SensorReader()

    # Take 10 readings with delay
    for i in range(10):
        sensor.display_reading(i)
        if i < 9:  # Don't delay after last reading
            sleep(MEASUREMENT_DELAY)

    print("\nSensor test complete!")


if __name__ == "__main__":
    main()
