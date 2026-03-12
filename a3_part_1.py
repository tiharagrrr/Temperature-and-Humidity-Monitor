"""
BME280 Sensor Reading Script
Student: Piyumi Tihara Egodage
ID: w1953194
Purpose: Read temperature, humidity, and pressure from BME280 sensor
"""

from machine import Pin, I2C
from time import sleep
import BME280
from datetime import datetime

# config constants
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0
I2C_FREQ = 40000
MEASUREMENT_DELAY = 5 # seconds

time = datetime.now()

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
            time = datetime.now()
            temp_str, press_str, hum_str = self.bme.values
            
            # Parse values (remove units)
            temperature = float(temp_str.replace('C', ''))
            pressure = float(press_str.replace('hPa', ''))
            humidity = float(hum_str.replace('%', ''))
            
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
        
        # Display formatted output
        print("=" * 50)
        displayTime = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Reading #{reading_num} at time {displayTime}")
        print("=" * 50)
        print(f"Temperature:    {temp:.2f} °C")
        print(f"Pressure:       {press:.2f} hPa")
        print(f"Humidity:       {hum:.2f} %")
        print("=" * 50)
        
        return {
            'temperature': temp,
            'pressure': press,
            'humidity': hum
        }

def main():
    print("\n" + "=" * 50)
    print("BME280 SENSOR TEST - PART A3")
    print("=" * 50 + "\n")
    
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
    
        