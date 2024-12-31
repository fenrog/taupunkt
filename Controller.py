#!/usr/bin/python3

"""
The controller responds to the seonso input and performs interactions on the data model object.
The controller receives the input, optionally validates it and then passes the input to the model.

Responsibility:
- Collects the environmental data of the RD200 and teh DHT22 seonsors and forwards it to the model.
Optional in future:
- Collect the in-fan-on information from the differential preassure monitor (low preasure pre warning)
- Collect the out-fan-off information from the differential preassure monitor (immeidate low preasure fan off)
"""


import threading
import time
from RD200 import RD200
from Dewpoint import Dewpoint


class Controller(threading.Thread):
    def __init__(self, model):
        threading.Thread.__init__(self)
        self.model = model
        self.should_stop = threading.Event() # create an unset event on init
        self.RD200 = RD200(self.on_change_RD200)
        self.DHT22 = Dewpoint(self.on_update_DHT22)

    def on_change_RD200(self, Bq, error):
        self.model.on_change_radon(Bq, error)

    def on_update_DHT22(self, averaged):
        self.model.on_update_dewpoints(averaged)

    def run(self):
        self.RD200.start()
        self.DHT22.start()
        while not self.should_stop.is_set():
            time.sleep(1)

    def stop(self):
        self.RD200.stop()
        self.DHT22.stop()
        self.should_stop.set()


def main():
    class Model():
        def on_change_radon(self, Bq, error):
            print(Bq, error)
        def on_update_dewpoints(self, timestamp, averaged):
            print(timestamp)
            for key in averaged:
                print("{:3s} {}".format(key, averaged[key]))
    model = Model()
    controller = Controller(model)
    controller.start()
    time.sleep(60*120)
    controller.stop()


if __name__ == '__main__':
    main()
