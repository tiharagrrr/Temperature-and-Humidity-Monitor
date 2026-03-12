"""
BME280 Sensor Reading Script
Student: Piyumi Tihara Egodage
ID: w1953194
Purpose: Read temperature, humidity, and pressure from BME280 sensor
"""

from machine import Pin, I2C
from time import sleep
import BME280

# config constants
I2C_SCL_PIN = 1
I2C_SDA_PIN = 0
I2C_FREQ = 40000
MEASUREMENT_DELAY = 2 # seconds

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
        
    def calculate_derived_values(self, temp, hum):
        """
        returns a dictionary with heat_index, dew point
        """
        # Valid for temp > 27°C and humidity > 40%
        if temp > 27 and hum > 40:
            heat_index = -8.78469475556 + 1.61139411 * temp + 2.33854883889 * hum
            heat_index += -0.14611605 * temp * hum - 0.012308094 * temp**2
            heat_index += -0.0164248277778 * hum**2 + 0.002211732 * temp**2 * hum
            heat_index += 0.00072546 * temp * hum**2 - 0.000003582 * temp**2 * hum**2
        else:
            heat_index = temp  # Use actual temperature
        
        # Dew Point (Magnus formula)
        a = 17.27
        b = 237.7
        alpha = ((a * temp) / (b + temp)) + (hum / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return {
            'heat_index': round(heat_index, 2),
            'dew_point': round(dew_point, 2)
        }
    
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
        
        # Calculate derived values
        derived = self.calculate_derived_values(temp, hum)
        
        # Display formatted output
        print("=" * 50)
        print(f"Reading #{reading_num}")
        print("=" * 50)
        print(f"Temperature:    {temp:.2f} °C")
        print(f"Pressure:       {press:.2f} hPa")
        print(f"Humidity:       {hum:.2f} %")
        print(f"Heat Index:     {derived['heat_index']:.2f} °C")
        print(f"Dew Point:      {derived['dew_point']:.2f} °C")
        print("=" * 50)
        
        return {
            'temperature': temp,
            'pressure': press,
            'humidity': hum,
            'heat_index': derived['heat_index'],
            'dew_point': derived['dew_point']
        }

def main():
    """Main execution function"""
    print("\n" + "=" * 50)
    print("BME280 SENSOR TEST - PART A1")
    print("=" * 50 + "\n")
    
    # Initialize sensor
    sensor = SensorReader()
    
    # Take 5 readings with delay
    for i in range(1, 6):
        sensor.display_reading(i)
        if i < 5:  # Don't delay after last reading
            sleep(MEASUREMENT_DELAY)
    
    print("\nSensor test complete!")

if __name__ == "__main__":
    main()
    
        