"""
BME280 Sensor Reading Script
Student: Piyumi Tihara Egodage
ID: w1953194
Purpose: Serve sensor readings via HTTP web interface
"""

import socket
import time

import BME280
import network
from machine import I2C, Pin

# Configs
WIFI_SSID = "Teow"
WIFI_PASSWORD = "meowww96"

# Alternative WiFi
WIFI_SSID_BACKUP = "ez WiFi"
WIFI_PASSWORD_BACKUP = "basicpassword123"

# Server Configuration
SERVER_PORT = 80
UPDATE_INTERVAL = 2  # seconds

# I2C Configuration
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.connected = False
        self.ip = None

    def connect(self, ssid, password, timeout=10):
        """Connects to wifi, returns True if connected, False otherwise"""
        print(f"\nConnecting to WiFi: {ssid}")
        self.wlan.connect(ssid, password)

        start_time = time.time()
        while not self.wlan.isconnected():
            if time.time() - start_time > timeout:
                print(f"Connection timeout for {ssid}")
                return False
            print(".", end="")
            time.sleep(0.5)

        self.connected = True
        self.ip = self.wlan.ifconfig()[0]
        print(f"\n✓ Connected! IP Address: {self.ip}")
        print(f"✓ Signal Strength: {self.wlan.status('rssi')} dBm")
        return True

    def connect_with_fallback(self):
        """Can be used to connect, including backup wifi connection"""
        if self.connect(WIFI_SSID, WIFI_PASSWORD):
            return True

        print("\nPrimary WiFi failed, trying backup...")
        return self.connect(WIFI_SSID_BACKUP, WIFI_PASSWORD_BACKUP)

    def get_signal_strength(self):
        """Get WiFi signal strength in dBm"""
        if self.connected:
            return self.wlan.status("rssi")
        return None


class BME280WebServer:
    def __init__(self):
        # Initialize sensor
        self.i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
        self.bme = BME280.BME280(i2c=self.i2c)

        # Initialize WiFi
        self.wifi = WiFiManager()

        self.readings_count = 0
        self.min_temp = float("inf")
        self.max_temp = float("-inf")
        self.start_time = time.time()

    def read_sensor(self):
        try:
            temp_str, press_str, hum_str = self.bme.values

            temp = float(temp_str.replace("C", ""))
            press = float(press_str.replace("hPa", ""))
            hum = float(hum_str.replace("%", ""))

            # Update statistics
            self.readings_count += 1
            self.min_temp = min(self.min_temp, temp)
            self.max_temp = max(self.max_temp, temp)

            return temp, press, hum
        except Exception as e:
            print(f"Sensor read error: {e}")
            return None, None, None

    def calculate_heat_index(self, temp, hum):
        """Calculate heat index"""
        if temp > 27 and hum > 40:
            hi = -8.78469475556 + 1.61139411 * temp + 2.33854883889 * hum
            hi += -0.14611605 * temp * hum - 0.012308094 * temp**2
            hi += -0.0164248277778 * hum**2 + 0.002211732 * temp**2 * hum
            hi += 0.00072546 * temp * hum**2 - 0.000003582 * temp**2 * hum**2
            return round(hi, 2)
        return round(temp, 2)

    def get_temp_status(self, temp):
        """Get temperature status and color"""
        if temp < 10:
            return "COLD", "#3498db"
        elif temp < 20:
            return "COOL", "#5dade2"
        elif temp < 25:
            return "COMFORTABLE", "#52be80"
        elif temp < 30:
            return "WARM", "#f39c12"
        else:
            return "HOT", "#e74c3c"

    def create_webpage(self):
        """Generate HTML page with live data"""
        temp, press, hum = self.read_sensor()

        if temp is None:
            return self.error_webpage()

        heat_index = self.calculate_heat_index(temp, hum)
        temp_status, temp_color = self.get_temp_status(temp)
        uptime = int(time.time() - self.start_time)
        signal = self.wifi.get_signal_strength()

        html = f"""<!DOCTYPE html>

<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{UPDATE_INTERVAL}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap" rel="stylesheet">
    <title>BME280 Sensor Dashboard</title>
    <style>
  :root{{
    --bg: #f6f8fb;
    --card: #ffffff;
    --muted: #6b7280;
    --accent: #2563eb;
    --accent-2: #06b6d4;
    --low: #0ea5e9;
    --normal: #16a34a;
    --high: #dc2626;
    --radius: 2px;
  }}

  *{{box-sizing:border-box}}
  body {{
    margin: 0;
    font-family: 'Plus Jakarta Sans', system-ui;
    background: linear-gradient(180deg, var(--bg), #eef2f7 80%);
    padding: 28px;
    display:flex;
    justify-content:center;
  }}
  .brand {{ display:flex; align-items:center; gap:12px; }}

  .logo {{ width:48px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent-2)); display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:20px;box-shadow:0 6px 20px rgba(37,99,235,0.18) }}

  .wrap {{ width: min(980px, 96%); }}

  .section-title{{
    font-size:16px;
    font-weight:600;
    margin:28px 0 12px;
  }}

  .header {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:18px; }}

  .grid-3 {{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap:16px;
  }}

  .grid-4 {{
    display:grid;
    grid-template-columns: repeat(4, 1fr);
    gap:16px;
  }}

  .card {{
    background:var(--card);
    padding:18px;
    border-radius:var(--radius);
    box-shadow:0 6px 18px rgba(15,23,42,0.06);
  }}

  .metric-label{{
    font-size:11px;
    color:var(--muted);
    font-family: "Geist Mono", monospace;
  }}
  h1{{font-size:16px;margin:0}}

  .metric-value{{
    font-size:15px;
    font-weight:400;
    margin-top:6px;
    font-family: "Geist Mono", monospace;
  }}

  .status-bar {{
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
}}

.status-item {{
    background: #f8f9fa;
    padding: 8px 15px;
    border-radius: 5px;
    font-size: 14px;
}}

  .badge{{
    display:inline-block;
    font-size:11px;
    padding:4px 8px;
    border-radius:20px;
    margin-top:8px;
    color:white;
  }}

  .sub{{color:var(--muted);font-size:12px}}

  .wide {{ grid-column: 1 / -1; display:flex;flex-direction:column;gap:12px; }}
  .muted {{ color: var(--muted); font-size:13px }}

  .footer {{text-align:right;color:var(--muted);font-size:14px}}

  .low{{ background:var(--low); }}
  .normal{{ background:var(--normal); }}
  .high{{ background:var(--high); }}

  @media (max-width: 900px){{
    .grid-4{{ grid-template-columns: repeat(3,1fr); }}
  }}

  @media (max-width: 800px){{
    .grid-4{{ grid-template-columns: repeat(2,1fr); }}
  }}

</style>
  </head>
  <body>
    <div class="wrap">
      <div class="header">
        <div class="brand">
          <div class="logo">IoT</div>
          <div>
            <h1>BME280 Environmental Monitoring Station</h1>
            <div class="sub">Real-time sensor data from Raspberry Pi Pico W for temperature, humidity & pressure</div>
          </div>
        </div>
        <div class="status-pill muted">Student ID:<strong style="color:var(--accent); margin-left:8px">w1953194</strong></div>
      </div>

            <div class="status-bar">
                <div class="status-item">
                    <strong>Status:</strong> <span style="color: #52be80;">● Online</span>
                </div>
                <div class="status-item">
                    <strong>Uptime:</strong> {uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s
                </div>
                <div class="status-item">
                    <strong>Readings:</strong> {self.readings_count}
                </div>
                <div class="status-item">
                    <strong>WiFi Signal:</strong> {signal} dBm
                </div>
                <div class="status-item">
                    <strong>Auto-refresh:</strong> {UPDATE_INTERVAL}s
                </div>
            </div>

<div class="section-title">Current Data</div>

<div class="grid-3">
  <div class="card">
    <div class="metric-label">Temperature</div>
    <div class="metric-value">{temp:.1f} °C</div>
    <span class="badge" style="background: {temp_color};">{temp_status}</span>
  </div>

  <div class="card">
    <div class="metric-label" >Humidity</div>
    <div class="metric-value">{hum:.1f} %</div>
    <span class="badge" style="background: {"#3498db" if 30 <= hum <= 60 else "#e67e22"};">
        {"OPTIMAL" if 30 <= hum <= 60 else "OUTSIDE COMFORT RANGE"}
    </span>
  </div>

  <div class="card">
    <div class="metric-label">Pressure</div>
    <div class="metric-value">{press:.1f} hPa</div>
    <span class="badge" style="background: #9b59b6;">
        {"HIGH" if press > 1013 else "LOW" if press < 1013 else "NORMAL"}
    </span>
  </div>
</div>

<!-- ADDITIONAL METRICS -->
<div class="section-title">Additional Metrics</div>

<div class="grid-4">
  <div class="card">
    <div class="metric-label">Heat Index</div>
    <div class="metric-value">{heat_index:.1f} °C</div>
  </div>

  <div class="card">
    <div class="metric-label">Max Temperature</div>
    <div class="metric-value">{self.max_temp:.1f} °C</div>
  </div>

  <div class="card">
    <div class="metric-label">Min Temperature</div>
    <div class="metric-value">{self.min_temp:.1f} °C</div>
  </div>

  <div class="card">
    <div class="metric-label">Temperature Range</div>
    <div class="metric-value">{(self.max_temp - self.min_temp):.1f} °C</div>
  </div>
</div>
      <div style="height:18px"></div>
      <p>Last updated: {time.localtime()[3]:02d}:{time.localtime()[4]:02d}:{time.localtime()[5]:02d}</p>
      <div class="footer">6NTCM009C: Internet of Things Coursework - Tihara Egodage</div>
    </div>
  </body>
</html> """

        return html

    def error_webpage(self):
        """Generate error page if sensor fails"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{UPDATE_INTERVAL}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap" rel="stylesheet">
    <title>Sensor Error</title>
    <style>
        body {
            font-family: 'Plus Jakarta Sans', system-ui;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #e74c3c;
            color: white;
            text-align: center;
        }
    </style>
</head>
<body>
    <div>
        <h1>⚠️ Sensor Error</h1>
        <p>Unable to read BME280 sensor data</p>
        <p>Please check sensor connections</p>
    </div>
</body>
</html>"""

    def start_server(self):
        if not self.wifi.connect_with_fallback():
            print("ERROR: Could not connect to any WiFi network!")
            return

        addr = socket.getaddrinfo("0.0.0.0", SERVER_PORT)[0][-1]
        s = socket.socket()  # creates tcp socket object
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)

        print(f"\n{'-' * 50}")
        print(f"🌐 Web Server Running!")
        print(f"{'-' * 50}")
        print(f"📱 Open in browser: http://{self.wifi.ip}")
        print(f"🔄 Auto-refresh every {UPDATE_INTERVAL} seconds")
        print(f"{'-' * 50}\n")

        # Server loop
        while True:
            try:
                cl, addr = s.accept()
                print(f"Client connected from {addr}")

                request = cl.recv(1024)
                request_str = request.decode("utf-8")

                html = self.create_webpage()
                response = "HTTP/1.1 200 OK\r\n"
                response += "Content=Type: text/html; charset=UTF-8\r\n"
                reponse += "Connection: close\r\n\r\n"
                response += html

                cl.send(response.encode("utf-8"))
                cl.close()

            except Exception as e:
                print(f"Server error {e}")
                try:
                    cl.close()
                except:
                    pass


def main():
    print("\n" + "-" * 50)
    print("BME280 WEB SERVER - PART A2")
    print("=" * 50 + "\n")

    server = BME280WebServer()
    server.start_server()


if __name__ == "__main__":
    main()
