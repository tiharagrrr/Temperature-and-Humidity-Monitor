BME280 IoT Project
=======================

A Python-based IoT project that retrieves temperature, humidity, and pressure readings from a BME280 sensor and displays them in the terminal, serves the data over a web server, and deploys it to a Google Sheets App Script.

**Table of Contents**
-----------------

1. [Getting Started](#getting-started)
2. [Requirements](#requirements)
3. [Project Structure](#project-structure)
4. [Usage](#usage)

**Getting Started**
------------------

To run the project, navigate to the `src` directory and run `python main.py`. This will prompt the user to select from the terminal display, web server and deploy to App Script.

**Requirements**
---------------

* Python 3.x
* BME280 library (install with `pip install python-bme280`)
* Flask library (install with `pip install flask`)
* Google Sheets App Script account (sign up for a free account on the [Google Cloud Console](https://console.cloud.google.com/))

**Project Structure**
--------------------

The project consists of the following files:

* `a1_basic_sensor.py`: Retrieves temperature, humidity, and pressure readings from the BME280 sensor.
* `a2_web_server.py`: Serves the sensor readings over a web server using Flask.
* `a3_part_1.py`: Deploys the data to a Google Sheets App Script.

**Usage**
-----

1. Run `python main.py` to start the project.
2. Open a web browser and navigate to `http://localhost:5000` to view the sensor readings in real-time.
3. Update the code in `a3_part_1.py` to deploy the data to your desired destination.
