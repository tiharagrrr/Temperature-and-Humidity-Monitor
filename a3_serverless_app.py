"""
BME280 Sensor Reading Script
Student: Piyumi Tihara Egodage
ID: w1953194
Purpose: Log timestamped sensor data to Google Sheets via Apps Script
"""

import json
import time

import BME280
import network
import urequests
from machine import I2C, RTC, Pin

# Google Apps Script Web App URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzU-tJwZFxqwbkq3znm4r4dSeVsUdauPLnOQBSAH0S1A9VQS4OmFh1R2j0FVBkqqt2HLQ/exec"

# WiFi Credentials
WIFI_SSID = "Teow"
WIFI_PASSWORD = "meowww96"

# Alternative WiFi
WIFI_SSID_BACKUP = "ez WiFi"
WIFI_PASSWORD_BACKUP = "basicpassword123"

# Logging Configuration
NUM_READINGS = 20  # Number of readings to take
READING_INTERVAL = 30  # Seconds between readings (30s = 10 min total for 20 readings)

# I2C Configuration
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0

# NTP Configuration
NTP_SERVER = "pool.ntp.org"
TIMEZONE_OFFSET = 5.5  # Adjust for your timezone (0 = UTC)
# =========================================


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.current_ssid = None

    def connect(self, ssid, password, timeout=15):
        print(f"\n🔌 Connecting to: {ssid}")

        # Disconnect if already connected
        if self.wlan.isconnected():
            self.wlan.disconnect()
            time.sleep(1)

        self.wlan.connect(ssid, password)

        start = time.time()
        while not self.wlan.isconnected():
            if time.time() - start > timeout:
                print(f"❌ Connection timeout for {ssid}")
                return False
            print(".", end="")
            time.sleep(0.5)

        self.current_ssid = ssid
        ip = self.wlan.ifconfig()[0]
        rssi = self.wlan.status("rssi")

        print(f"\n✅ Connected to {ssid}")
        print(f"   IP: {ip}")
        print(f"   Signal: {rssi} dBm")

        return True

    def connect_with_fallback(self):
        """Try primary, then backup WiFi"""
        networks = [
            (WIFI_SSID, WIFI_PASSWORD),
            (WIFI_SSID_BACKUP, WIFI_PASSWORD_BACKUP),
        ]

        for ssid, password in networks:
            if self.connect(ssid, password):
                return True

        return False

    def is_connected(self):
        """Check if still connected"""
        return self.wlan.isconnected()

    def reconnect(self):
        """Attempt to reconnect using current credentials"""
        if self.current_ssid:
            print("\n🔄 Attempting reconnection...")
            return self.connect_with_fallback()
        return False

    def get_signal_strength(self):
        """Get current signal strength"""
        if self.is_connected():
            return self.wlan.status("rssi")
        return None


class TimeManager:
    """Manage time synchronization via NTP"""

    def __init__(self):
        self.rtc = RTC()
        self.synced = False

    def sync_time(self, max_retries=3):
        """Synchronize time with NTP server"""
        import ntptime

        print("\n🕐 Synchronizing time with NTP...")

        for attempt in range(max_retries):
            try:
                ntptime.host = NTP_SERVER
                ntptime.settime()
                self.synced = True

                current_time = time.localtime()
                print(
                    f"✅ Time synced: {current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d} "
                    f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
                )
                return True

            except Exception as e:
                print(f"❌ NTP sync attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        print("⚠️  Continuing with system time (may be inaccurate)")
        return False

    def get_timestamp(self):
        """Get current timestamp string"""
        t = time.localtime()
        return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"


class SensorManager:
    """Manage BME280 sensor"""

    def __init__(self):
        self.i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
        self.bme = BME280.BME280(i2c=self.i2c)
        print("✅ BME280 sensor initialized")

    def read(self):
        """Read sensor with error handling"""
        try:
            temp_str, press_str, hum_str = self.bme.values

            temp = float(temp_str.replace("C", ""))
            press = float(press_str.replace("hPa", ""))
            hum = float(hum_str.replace("%", ""))

            return temp, press, hum

        except Exception as e:
            print(f"❌ Sensor read error: {e}")
            return None, None, None

    def get_full_reading(self):
        """Get all sensor data including calculations"""
        temp, press, hum = self.read()

        if temp is None:
            return None

        return {
            "temperature": round(temp, 2),
            "pressure": round(press, 2),
            "humidity": round(hum, 2),
        }


class GoogleSheetsLogger:
    """Log data to Google Sheets with retry logic"""

    def __init__(self, script_url, wifi_manager):
        self.script_url = script_url
        self.wifi = wifi_manager
        self.failed_uploads = []  # Buffer for failed uploads
        self.upload_count = 0
        self.retry_delays = [2, 5, 10]  # Exponential backoff delays

    def upload_data(self, data, max_retries=3):
        """
        Upload data to Google Sheets with retry logic
        Returns: True if successful, False otherwise
        """
        # Ensure WiFi is connected
        if not self.wifi.is_connected():
            print("⚠️  No WiFi connection, attempting reconnect...")
            if not self.wifi.reconnect():
                print("❌ Failed to reconnect to WiFi")
                self.failed_uploads.append(data)
                return False

        # Try uploading with retries
        for attempt in range(max_retries):
            try:
                print(
                    f"\n📤 Uploading to Google Sheets (attempt {attempt + 1}/{max_retries})..."
                )

                # Prepare JSON payload
                json_data = json.dumps(data)
                headers = {"Content-Type": "application/json"}

                # Make POST request
                response = urequests.post(
                    self.script_url, data=json_data, headers=headers, timeout=10
                )

                # Check response
                if response.status_code == 200 or response.status_code == 302:
                    result = response.json()
                    response.close()

                    if result.get("status") == "success":
                        self.upload_count += 1
                        print(f"✅ Upload successful! Entry #{result.get('entry')}")
                        return True
                    else:
                        print(f"⚠️  Server returned error: {result.get('message')}")
                else:
                    print(f"⚠️  HTTP {response.status_code}: {response.text}")
                    response.close()

            except Exception as e:
                print(f"❌ Upload error: {e}")

            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        # All retries failed - buffer the data
        print("❌ All upload attempts failed - data buffered for later")
        self.failed_uploads.append(data)
        return False

    def retry_failed_uploads(self):
        """Attempt to upload any buffered failed uploads"""
        if not self.failed_uploads:
            return

        print(
            f"\n🔄 Attempting to upload {len(self.failed_uploads)} buffered readings..."
        )

        successful = []
        for data in self.failed_uploads:
            if self.upload_data(data, max_retries=2):
                successful.append(data)

        # Remove successful uploads from buffer
        for data in successful:
            self.failed_uploads.remove(data)

        remaining = len(self.failed_uploads)
        if remaining > 0:
            print(f"⚠️  {remaining} readings still pending")
        else:
            print("✅ All buffered readings uploaded!")


class DataCollector:
    """Main data collection orchestrator"""

    def __init__(self):
        self.wifi = WiFiManager()
        self.time_mgr = TimeManager()
        self.sensor = SensorManager()
        self.logger = GoogleSheetsLogger(GOOGLE_SCRIPT_URL, self.wifi)

        # Statistics tracking
        self.readings = []
        self.start_time = None

    def initialize(self):
        """Initialize all systems"""
        print("\n" + "=" * 60)
        print("BME280 GOOGLE SHEETS LOGGER - PART A3")
        print("=" * 60)

        # Connect to WiFi
        if not self.wifi.connect_with_fallback():
            print("\n❌ Error: Could not connect to WiFi")
            return False

        # Sync time
        self.time_mgr.sync_time()

        return True

    def collect_reading(self, reading_num):
        """Collect and upload a single reading"""
        print(f"\n{'─' * 60}")
        print(f"READING #{reading_num}/{NUM_READINGS}")
        print(f"{'─' * 60}")

        # Get timestamp
        timestamp = self.time_mgr.get_timestamp()
        print(f"Timestamp: {timestamp}")

        # Read sensor
        data = self.sensor.get_full_reading()

        if data is None:
            print("❌ Failed to read sensor")
            return False

        # Display readings
        print(f" Temperature: {data['temperature']}°C")
        print(f"Humidity: {data['humidity']}%")
        print(f"Pressure: {data['pressure']} hPa")

        # Store for statistics
        self.readings.append(data)

        # Upload to Google Sheets
        success = self.logger.upload_data(data)

        # Try to upload any previously failed readings
        if success and self.logger.failed_uploads:
            self.logger.retry_failed_uploads()

        return True

    def calculate_statistics(self):
        """Calculate and display statistics"""
        if not self.readings:
            return

        temps = [r["temperature"] for r in self.readings]

        print("\n" + "=" * 60)
        print("📈 FINAL STATISTICS")
        print("=" * 60)
        print(f"Total Readings: {len(self.readings)}")
        print(f"Successful Uploads: {self.logger.upload_count}")
        print(f"Failed Uploads: {len(self.logger.failed_uploads)}")
        print("\nTemperature Statistics:")
        print(f"  Minimum: {min(temps):.2f}°C")
        print(f"  Maximum: {max(temps):.2f}°C")
        print(f"  Average: {sum(temps) / len(temps):.2f}°C")
        print(f"  Range: {max(temps) - min(temps):.2f}°C")

        # Find min and max with timestamps
        min_idx = temps.index(min(temps))
        max_idx = temps.index(max(temps))

        print(f"\nMin occurred at reading #{min_idx + 1}")
        print(f"Max occurred at reading #{max_idx + 1}")
        print("=" * 60)

    def run(self):
        """Main execution loop"""
        if not self.initialize():
            return

        self.start_time = time.time()

        # Collect readings
        for i in range(1, NUM_READINGS + 1):
            self.collect_reading(i)

            # Wait before next reading (except for last one)
            if i < NUM_READINGS:
                print(f"\n⏳ Waiting {READING_INTERVAL} seconds until next reading...")
                time.sleep(READING_INTERVAL)

        # Show final statistics
        self.calculate_statistics()

        # Final retry for any failed uploads
        if self.logger.failed_uploads:
            print("\n🔄 Final attempt to upload pending readings...")
            self.logger.retry_failed_uploads()

        duration = time.time() - self.start_time
        print(
            f"\n✅ Data collection complete! Duration: {int(duration // 60)}m {int(duration % 60)}s"
        )


def main():
    """Entry point"""
    collector = DataCollector()
    collector.run()


if __name__ == "__main__":
    main()
