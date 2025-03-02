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
import math
import time
import json
import board
import adafruit_dht
from datetime import datetime, timezone


READ_TICK = 20  # read every n seconds
CONFIG_FILE = r"DHT22.json"


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
        with open(CONFIG_FILE) as f:
            self.config = json.load(f)

        for key in self.config:
            self.config[key]["offset"] = {float(k): v for k, v in self.config[key]["offset"].items()}
            for temperature in self.config[key]["offset"]:
                self.config[key]["offset"][temperature] = {float(k): v for k, v in self.config[key]["offset"][temperature].items()}

        # Initial the dht devices, with data pins connected to:
        self.dhtDevice = {}
        for key in self.config:
            self.dhtDevice[key] = adafruit_dht.DHT22(id2pin(self.config[key]["pin"]))

        self.timer = TimeSyncedTimer(READ_TICK, self.update_data)
        self.timer.start()

    def get_offset(self, key, temperature, humidity):
        # temperature range -40 °C .. + 80 °C
        # humidity range: 0% .. 100%
        # temperature normalization: t_normalized = (temperature + 40) / (80 - -40) = (temperature + 40) / 120
        # humidity normalization:    h_normalized = (humidity - 0 ) / (100 - 0) = humidity / 100

        t_offset = 0.0
        h_offset = 0.0

        if (key in self.config) and ("offset" in self.config[key]):
            if len(self.config[key]["offset"]):
                t_delta = +80 - (-40)  # maximum temperature delta
                h_delta = 100 - 0    # maximum humidity delta
                max_distance = math.sqrt((t_delta * t_delta) + (h_delta * h_delta))
                t_index = None
                h_index = None

                for t in self.config[key]["offset"]:
                    for h in self.config[key]["offset"][t]:
                        t_delta = t - temperature
                        h_delta = h - humidity
                        distance = math.sqrt((t_delta * t_delta) + (h_delta * h_delta))
                        if max_distance >= distance:
                            max_distance = distance
                            t_index = t
                            h_index = h
                if t_index is not None:
                    t_offset = self.config[key]["offset"][t_index][h_index]["temperature"]
                    h_offset = self.config[key]["offset"][t_index][h_index]["humidity"]
            else:
                print("ERROR: no offsets available")
                pass
        else:
            print("ERROR: no data available, keep default")
            pass  # no data available, keep default
        return t_offset, h_offset

    def update_data(self):
        data = {}
        for key in self.dhtDevice:
            data[key] = {}
            try_again = True
            tries = 0
            while try_again:
                try_again = False
                tries += 1
                try:
                    data[key]["temperature"] = self.dhtDevice[key].temperature
                    data[key]["humidity"] = self.dhtDevice[key].humidity
                    if (0.0 == data[key]["temperature"]) and (0.0 == data[key]["humidity"]):
                        print(f"Nonsense data, most likely [0x00, 0x00, 0x00, 0x00, 0x00] has been 'received' from a non present sensor at '{key}'")
                        raise Exception(f"Nonsense data, most likely [0x00, 0x00, 0x00, 0x00, 0x00] has been 'received' from a non present sensor at '{key}'")
                    if (-40.0 > data[key]["temperature"]) or (+45 < data[key]["temperature"]):
                        print(f"temperature {data[key]['temperature']} is out of range for sensor at '{key}'")
                        raise Exception(f"temperature {data[key]['temperature']} is out of range for sensor at '{key}'")
                    print("{:18.7f} {:3s} {:5.2f}°C {:5.2f}%".format(time.time(), key, data[key]["temperature"], data[key]["humidity"]))
                    if self.offset_correction:
                        t_offset, h_offset = self.get_offset(key, data[key]["temperature"], data[key]["humidity"])
                        data[key]["temperature"] += t_offset
                        data[key]["humidity"] += h_offset
                    data[key]["utc"] = datetime.now(timezone.utc)
                    data[key]["error"] = False
                except Exception as e:
                    # Errors happen fairly often, DHT's are hard to read, ensure the data is set to invalud
                    data[key] = {"temperature": None, "humidity": None, "utc": None, "error": True}
                    if ("Try again" in str(e)) and (tries < 3):
                        try_again = True
                    if self.verbose:
                        print(key, e)

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
        for k, v in data.items():
            if v["temperature"] is not None:
                raw_data[k]["temperature"].append(v["temperature"])
            if v["humidity"] is not None:
                raw_data[k]["humidity"].append(v["humidity"])

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    raw_data = {}
    avg_data = {}
    for key in config:
        raw_data[key] = {"temperature": [], "humidity": []}
        avg_data[key] = {"temperature": None, "humidity": None}
        if "t_offset" in config[key]:
            del config[key]["t_offset"]
        if "r_offset" in config[key]:
            del config[key]["r_offset"]
        if "offset" not in config[key]:
            config[key]["offset"] = {} # two dimensional dict, organized by temperature and humidity
        config[key]["offset"] = {float(k): v for k, v in config[key]["offset"].items()}
        for temperature in config[key]["offset"]:
            config[key]["offset"][temperature] = {float(k): v for k, v in config[key]["offset"][temperature].items()}

    dht = DHT22(callback, offset_correction=False, verbose=True)
    time.sleep(minutes * 60)
    dht.exit()
    time.sleep(READ_TICK + 1)

    sum_t = 0.0
    sum_h = 0.0
    cnt = 0
    for k, v in raw_data.items():
        min_t = min(v["temperature"])
        max_t = max(v["temperature"])
        avg_data[k]["temperature"] = sum(v["temperature"]) / len(v["temperature"])
        sum_t += avg_data[k]["temperature"]
        min_h = min(v["humidity"])
        max_h = max(v["humidity"])
        avg_data[k]["humidity"] = sum(v["humidity"]) / len(v["humidity"])
        sum_h += avg_data[k]["humidity"]
        print(k, "t ", min_t, max_t, avg_data[k]["temperature"], "rH", min_h, max_h, avg_data[k]["humidity"])
        cnt += 1

    avg_t = sum_t / cnt
    avg_h = sum_h / cnt
    print(avg_t, avg_h)

    for key in config:
        avg_t_rounded = round(avg_data[key]["temperature"], 1)
        avg_h_rounded = round(avg_data[key]["humidity"], 1)
        if avg_t_rounded not in config[key]["offset"]:
            config[key]["offset"][avg_t_rounded] = {}
        config[key]["offset"][avg_t_rounded][avg_h_rounded] = {
            "temperature": avg_t - avg_data[key]["temperature"],
            "humidity": avg_h - avg_data[key]["humidity"],
        }

    for key in config:
        config[key]["pin"] = int(str(config[key]["pin"]))
        config[key]["offset"] = dict(sorted(config[key]["offset"].items()))
        for temperature in config[key]["offset"]:
            config[key]["offset"][temperature] = dict(sorted(config[key]["offset"][temperature].items()))


    with open(CONFIG_FILE, 'w') as f:
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
    demo(1)


if __name__ == '__main__':
    main()
