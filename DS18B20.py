#!/usr/bin/python3

"""
Based on the article: https://RandomNerdTutorials.com/raspberry-pi-ds18b20-python/
Based on the Adafruit example: https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/Raspberry_Pi_DS18B20_Temperature_Sensing/code.py

The module delivers the averaged temperature of the five air streams.

Five DS18B20 sensors are located in the four in- and outlet air streams of the heat exchanger and in the inlet air stream of the heater.
The sensors share one common bus. They are connected to
- GND    (RPi header pin 6, 9, 14, 20, 25, 30, 34 or 39)
- 3.3V   (RPi header pin 1 or 17)
- GPIO_4 (RPi header pin 7)
- A 4.7k pullup resistor is connected between GPIO_4 and 3.3V.
One trunaround time to capture all 5 sensors is about 5 seconds.

Responsibility:
- for each DS18B20 sensor
-- calculate a moving average for one minute for the temperature in °C
- a callback is called on minute change to announce the averaged values of the last minute

Architecture:
- uses data provided in the file system that is provided by the modules w1-gpio in cooperation with w1-therm
- action is driven by ...
- the caller registers a callback uppon instantiation
- main is for demonstration

Model responsibility:
- The "Fortluft" temperature is relevant to judge whether the heat exchanger is about to freeze. If so, the heater is to be enabled.
"""

from TimeSyncedTimer import TimeSyncedTimer
import os
#import glob
import time
import json
from datetime import datetime, timezone
from Dewpoint import calc_avg

#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')


READ_TICK = 20                 # read every n seconds
assert(0 == (60 % READ_TICK))  # ensure the seconds of a minute can be evenly divided by the seconds between two reads
NUM_SAMPLES = 60 // READ_TICK  # number of samples regarded for averaging

CONFIG_FILE = r"DS18B20.json"

DEVICE_DIR = '/sys/bus/w1/devices/'


class DS18B20():
    def __init__(self, on_update, verbose=False):
        self.on_update = on_update
        self.verbose = verbose
        with open(CONFIG_FILE) as f:
            self.config = json.load(f)
        self.raw_data = {}
        self.averaged = {}
        self.timer = TimeSyncedTimer(READ_TICK, self.update_data)

    def read_temp_raw(self, device_file):
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_temp(self, device_file):
        lines = self.read_temp_raw(device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw(device_file)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            # temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c #, temp_f

    def capture_data(self):
        data = {}
        for sensor in self.config:
            device_file = os.path.join(DEVICE_DIR, sensor, "w1_slave")
            long_name = self.config[sensor]["long"]
            short_name = self.config[sensor]["short"]
            try:
                temp_c = self.read_temp(device_file)
                data[short_name] = {
                    "temperature": temp_c,
                    "error": False,
                }
                if self.verbose:
                    print(sensor, device_file, os.path.isfile(device_file), short_name, long_name, temp_c)
            except Exception as e:
                data[short_name] = {
                    "temperature": None,
                    "error": True,
                }
                if self.verbose:
                    print(sensor, device_file, os.path.isfile(device_file), short_name, long_name, e)
        return data

    def average_data(self, data):
        for key in data:
            if key not in self.averaged:
                self.averaged[key] = {}
            if key not in self.raw_data:
                self.raw_data[key] = {
                    "temperature": [None] * NUM_SAMPLES,
                }
            if not data[key]["error"]:
                self.raw_data[key]["temperature"].append(data[key]["temperature"])
            else:
                self.raw_data[key]["temperature"].append(None)
            self.raw_data[key]["temperature"].pop(0)
            assert NUM_SAMPLES == len(self.raw_data[key]["temperature"])

        for key in self.raw_data:
            temperature = calc_avg(self.raw_data[key]["temperature"])
            if (temperature is not None):
                self.averaged[key]["temperature"] = round(temperature, 1)
                self.averaged[key]["error"] = False
            else:
                self.averaged[key]["temperature"] = None
                self.averaged[key]["error"] = True

    def update_data(self):
        data = self.capture_data()
        self.average_data(data)
        self.on_update(self.averaged)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.cancel()


def demo(minutes):
    def on_update(data):
        for key in data:
            if not data[key]["error"]:
                print("{:15s} {:-4.1f}°C".format(key, data[key]["temperature"]))
            else:
                print("{:15s} error".format(key))

    ds = DS18B20(on_update, verbose = True)
    ds.start()
    time.sleep(minutes * 60)
    ds.stop()


def main():
    demo(2)


if __name__ == '__main__':
    main()
