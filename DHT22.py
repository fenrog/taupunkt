#!/usr/bin/env python3

"""
One external sensor is located outside the cellar romm "NO" and named "ext".
Four senssors are located inside in four cellar rooms named "NO", "SO", "SW", "NW".

Responsibility:
- for each DHT22 sensor:
-- cyclically read the sensor every READ_TICK seconds
-- add sensor specific offsets to the raw raw temparature and relative humidity data
-- in case of read error for a sensor, immediate retries lead to invalid data, thus no immediate retries
-- in case all retries failed, set an error flag
- a callback is called every READ_TICK seconds with the data as dictionary

Architecture:
- excuted in a timer
- the caller registers a callback uppon instantiation
- main is for calibration and demonstration
"""

from TimeSyncedTimer import TimeSyncedTimer
import time
import json
import board
import adafruit_dht
from datetime import datetime, timezone


READ_TICK = 20  # read every n seconds


def id2pin(id):
    lookup = {
        0: board.D0,
        1: board.D1,
        2: board.D2,
        3: board.D3,
        4: board.D4,
        5: board.D5,
        6: board.D6,
        7: board.D7,
        8: board.D8,
        9: board.D9,
        10: board.D10,
        11: board.D11,
        12: board.D12,
        13: board.D13,
        14: board.D14,
        15: board.D15,
        16: board.D16,
        17: board.D17,
        18: board.D18,
        19: board.D19,
        20: board.D20,
        21: board.D21,
        22: board.D22,
        23: board.D23,
        24: board.D24,
        25: board.D25,
        26: board.D26,
        27: board.D27,
    }
    return lookup[id]  # explode if not found


class DHT22():
    def __init__(self, callback, offset_correction=True, verbose=False):
        self.callback = callback
        self.offset_correction = offset_correction
        self.verbose = verbose
        with open('DHT22.json') as f:
            self.config = json.load(f)

        # Initial the dht devices, with data pins connected to:
        self.dhtDevice = {}
        for key in self.config:
            self.dhtDevice[key] = adafruit_dht.DHT22(id2pin(self.config[key]["pin"]))

        self.timer = TimeSyncedTimer(READ_TICK, self.update_data)
        self.timer.start()

    def update_data(self):
        data = {}
        for key in self.dhtDevice:
            data[key] = {}
            try:
                data[key]["temperature"] = self.dhtDevice[key].temperature
                data[key]["humidity"] = self.dhtDevice[key].humidity
                if self.offset_correction:
                    data[key]["temperature"] += self.config[key]["t_offset"]
                    data[key]["humidity"] += self.config[key]["r_offset"]
                data[key]["utc"] = datetime.now(timezone.utc)
                data[key]["error"] = False
            except Exception as error:
                # Errors happen fairly often, DHT's are hard to read, ensure the data is set to invalud
                data[key] = {"temperature": None, "humidity": None, "utc": None, "error": True}
                if self.verbose:
                    print(key, error.args[0])

        self.callback(data)

    def exit(self):
        self.timer.cancel()
        for key in self.dhtDevice:
            self.dhtDevice[key].exit()


def train_offsets(minutes):
    global READ_TICK
    READ_TICK_BAK = READ_TICK
    READ_TICK = 2   # the sensor or the library (?) updates ervery two seconds

    def callback(data):
        t = 0.0
        r = 0.0
        cnt = 0
        for key in data:
            if not data[key]["error"]:
                print("{:3s} {:-4.1f}°C {:-4.1f}%".format(key, data[key]["temperature"], data[key]["humidity"]))
                t += data[key]["temperature"]
                r += data[key]["humidity"]
                cnt += 1
            else:
                print("{:3s} error".format(key))
                errors[key] += 1

        if cnt:
            t_avg = t / cnt  # calculate average
            r_avg = r / cnt  # calculate average
            for key in data:
                if not data[key]["error"]:
                    deviation_t[key].append(t_avg - data[key]["temperature"])
                    deviation_r[key].append(r_avg - data[key]["humidity"])


    config = {
        "ext": {"pin": board.D24, "t_offset":0, "r_offset": 0},
        "NO": {"pin": board.D23, "t_offset":0, "r_offset": 0},
        "SO": {"pin": board.D25, "t_offset":0, "r_offset": 0},
        "NW": {"pin": board.D27, "t_offset":0, "r_offset": 0},
        "SW": {"pin": board.D26, "t_offset":0, "r_offset": 0},
    }
    deviation_t = {}
    deviation_r = {}
    errors = {}
    for key in config:
        deviation_t[key] = []
        deviation_r[key] = []
        errors[key] = 0

    dht = DHT22(callback, offset_correction=False, verbose=True)
    time.sleep(minutes * 60)
    dht.exit()

    for key in config:
        if len(deviation_t[key]):
            config[key]["t_offset"] = sum(deviation_t[key]) / len(deviation_t[key])
        if len(deviation_r[key]):
            config[key]["r_offset"] = sum(deviation_r[key]) / len(deviation_r[key])
        print(key, errors[key], len(deviation_t[key]), len(deviation_r[key]), config[key])

    for key in config:
        config[key]["pin"] = int(str(config[key]["pin"]))
        print("{} errors {}".format(key, errors[key]))
    with open('DHT22.json', 'w') as f:
        json.dump(config, f, indent=2)

    READ_TICK = READ_TICK_BAK


def demo(minutes):
    def callback(data):
        for key in data:
            if not data[key]["error"]:
                print("{:3s} {} {:-4.1f}°C {:-4.1f}%".format(key, data[key]["utc"], data[key]["temperature"], data[key]["humidity"]))
            else:
                print("{:3s} error".format(key))

    dht = DHT22(callback, verbose=True)
    time.sleep(minutes * 60)
    dht.exit()


def main():
#    train_offsets(1)
    demo(10)


if __name__ == '__main__':
    main()
