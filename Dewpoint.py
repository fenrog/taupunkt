#!/usr/bin/env python3

"""
The module delivers the averaged temperature and relative humidityof the external sensor and teh group of teh internal sensors.

Responsibility:
- for each DHT22 sensor:
-- calculate a moving average for one minute for the temperature in °C
-- calculate a moving average for one minute for the relative humidity in % as float
-- calculate the dewpoint based on the averaged temperature and relative humidity in °C
- a callback is called on minute change to announce the averaged values of the last minute

Architecture:
- uses DHT22 to capture the raw data
- action is driven by the callback that is cyclically called from DHT22 uppon data update
- the caller registers a callback uppon instantiation
- main is for demonstration
"""


import time
import numpy as np
from datetime import datetime, timedelta, timezone
from DHT22 import DHT22, READ_TICK

assert(0 == (60 % READ_TICK))  # ensure the seconds of a minute can be evenly divided by the seconds between two reads
NUM_SAMPLES = 60 // READ_TICK  # number of samples regarded for averaging


def calc_dewpoint(t: float, r: float) -> float:
    if (t >= 0):
        a = 7.5
        b = 237.3
    else:
        a = 7.6
        b = 240.7

    # Sättigungsdampfdruck in hPa
    sdd = 6.1078 * np.power(10, (a*t)/(b+t))

    # Dampfdruck in hPa
    dd = sdd * (r/100)

    # v-Parameter
    v = np.log10(dd/6.1078)

    # Taupunkttemperatur (°C)
    tt = (b*v) / (a-v)
    return float(tt)


def calc_avg(a_list):
    sum = 0.0
    cnt = 0
    for val in a_list:
        if val is not None:
            sum += val
            cnt += 1
    if cnt:
        return sum / cnt
    else:
        return None


class Dewpoint():
    def __init__(self, on_update):
        self.on_update = on_update
        self.sensors = None
        self.raw_data = {}
        self.averaged = {}

    def callback(self, data):
        """callback for DHT22"""
        for key in data:
            # averaging
            if key not in self.averaged:
                self.averaged[key] = {}
            if key not in self.raw_data:
                self.raw_data[key] = {
                    "temperature": [None] * NUM_SAMPLES,
                    "humidity": [None] * NUM_SAMPLES,
                }
            if not data[key]["error"]:
                self.raw_data[key]["temperature"].append(data[key]["temperature"])
                self.raw_data[key]["humidity"].append(data[key]["humidity"])
            else:
                self.raw_data[key]["temperature"].append(None)
                self.raw_data[key]["humidity"].append(None)
            self.raw_data[key]["temperature"].pop(0)
            self.raw_data[key]["humidity"].pop(0)
            assert NUM_SAMPLES == len(self.raw_data[key]["temperature"])
            assert NUM_SAMPLES == len(self.raw_data[key]["humidity"])

        for key in self.raw_data:
            temperature = calc_avg(self.raw_data[key]["temperature"])
            humidity = calc_avg(self.raw_data[key]["humidity"])
            if (temperature is not None) and (humidity is not None):
                self.averaged[key]["temperature"] = round(temperature, 1)
                self.averaged[key]["humidity"] = round(humidity, 1)
                self.averaged[key]["dewpoint"] = round(calc_dewpoint(temperature, humidity), 1)
                self.averaged[key]["error"] = False
            else:
                self.averaged[key]["temperature"] = None
                self.averaged[key]["humidity"] = None
                self.averaged[key]["dewpoint"] = None
                self.averaged[key]["error"] = True

        self.on_update(self.averaged)

    def start(self):
        self.sensors = DHT22(self.callback)

    def stop(self):
       self.sensors.exit()


def demo(minutes):
    def on_update(averaged):
        for key in averaged:
            print("{:3s} {}".format(key, averaged[key]))

    dewpoint = Dewpoint(on_update)
    dewpoint.start()
    time.sleep(minutes * 60)
    dewpoint.stop()


def main():
    demo(5)


if __name__ == '__main__':
    main()
