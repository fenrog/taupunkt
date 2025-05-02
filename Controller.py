#!/usr/bin/python3

"""
The controller responds to the sensor input and performs interactions on the data model object.
The controller receives the input, optionally validates it and then passes the input to the model.

Responsibility:
- Collects the environmental data of the RD200, the DHT22, and the DS18B20 sensors and forwards it to the model.
"""


import threading
import time
from RD200 import RD200
from Dewpoint import Dewpoint
from DS18B20 import DS18B20


class Controller(threading.Thread):
    def __init__(self, model):
        threading.Thread.__init__(self)
        self.model = model
        self.should_stop = threading.Event() # create an unset event on init
        self.RD200 = RD200(self.on_update_RD200)
        self.DHT22 = Dewpoint(self.on_update_DHT22)
        self.DS18B20 = DS18B20(self.on_update_DS18B20)

    def on_update_RD200(self, Bq, error):
        self.model.on_update_radon(Bq, error)

    def on_update_DHT22(self, averaged):
        self.model.on_update_dewpoints(averaged)

    def on_update_DS18B20(self, averaged):
        self.model.on_update_air_stream_temperatures(averaged)

    def run(self):
        self.RD200.start()
        self.DHT22.start()
        self.DS18B20.start()
        while not self.should_stop.is_set():
            time.sleep(1)

    def stop(self):
        self.RD200.stop()
        self.DHT22.stop()
        self.DS18B20.stop()
        self.should_stop.set()


def main():
    class Model():
        def on_update_radon(self, Bq, error):
            print(Bq, error)
        def on_update_dewpoints(self, averaged):
            for key in averaged:
                print("{:3s} {}".format(key, averaged[key]))
        def on_update_air_stream_temperatures(self, averaged):
            for key in averaged:
                print("{:3s} {}".format(key, averaged[key]))
    model = Model()
    controller = Controller(model)
    controller.start()
    time.sleep(60*120)
    controller.stop()


if __name__ == '__main__':
    main()
