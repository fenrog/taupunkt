import threading
import queue
import time
import gpiod
from rpi_rf_gpiod import RFDevice

GPIO = 17

"""
intended to be used with https://www.amazon.de/gp/product/B0BZJBPTB7

required externalpackages:
- https://github.com/wiringpi/wiringpi
- https://github.com/ninjablocks/433Utils.git

how to get the code:
- connect the receiver to GPIO_18, +5V and GND
- execute ./433Utils/RPi_utils/RFSniffer
- press the on button of the remote control and note down the on_code
- press the off button of the remote control and note down the off_code
"""


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RpiRfGpiod(threading.Thread, metaclass=Singleton):
    total_running = 0

    def __init__(self, verbose=False):
        threading.Thread.__init__(self)
        self.verbose = verbose
        self.max_repetitions = 3
        self.chip = gpiod.Chip("gpiochip0")
        self.gpio = self.chip.get_line(GPIO)
        self.rfdevice = RFDevice(self.gpio)
        self.rfdevice.tx_repeat = 4
        self.gpio.request(consumer="rpi-rf_send", type=gpiod.LINE_REQ_DIR_OUT)
        self.should_stop = threading.Event() # create an unset event on init
        self.q = queue.Queue()

    def put(self, code):
        self.q.put(code)

    def run(self):
        while not self.should_stop.is_set() or not self.q.empty():
            code = self.q.get()
            repetitions = 0
            while repetitions < self.max_repetitions:
                t_start = time.time()
                result = self.rfdevice.tx_code(code)
                t_end = time.time()
                if result:
                    if self.verbose:
                        print(int(time.time()), repetitions, result, code, t_end - t_start)
                    break
                else:
                    if self.verbose:
                        print(int(time.time()), repetitions, result, code, t_end - t_start)
                    time.sleep(0.1)
                    repetitions += 1
            if repetitions == self.max_repetitions:
                print("ERROR: final timeout", code)

    def start(self):
        if 0 == RpiRfGpiod.total_running:
            threading.Thread.start(self)
        RpiRfGpiod.total_running += 1

    def stop(self):
        if RpiRfGpiod.total_running:
            RpiRfGpiod.total_running -= 1
        if 0 == RpiRfGpiod.total_running:
            self.should_stop.set()


class Switch(threading.Thread):
    def __init__(self, on_code, off_code, verbose=False):
        threading.Thread.__init__(self)
        self.on_code = on_code
        self.off_code = off_code
        self.verbose = verbose
        self.is_on = False
        self.should_stop = threading.Event() # create an unset event on init
        self.rpi_rf_gpiod = RpiRfGpiod(verbose=verbose)

    def on(self):
        if not self.is_on:
            self.is_on = True
            self.t_next_transmission = time.time() # transmit asap
            if self.verbose:
                print(int(self.t_next_transmission), f"on({self.on_code})")

    def off(self):
        if self.is_on:
            self.is_on = False
            self.t_next_transmission = time.time() # transmit asap
            if self.verbose:
                print(int(self.t_next_transmission), f"off({self.off_code})")

    def transmit(self):
        self.rpi_rf_gpiod.put(self.on_code if self.is_on else self.off_code)

    def run(self):
        self.t_next_transmission = time.time()
        while not self.should_stop.is_set():
            if time.time() >= self.t_next_transmission:
                self.t_next_transmission += 60  # next desired transmission in 60 seconds
                self.transmit()

            t_sleep = self.t_next_transmission - time.time()
            if t_sleep > 0.1:
                t_sleep = 0.1  # do not wait longer than one second in order to stop asap
            if t_sleep < 0:
               t_sleep = 0  # avoid exception due to negative time
            time.sleep(t_sleep)
        self.transmit() # take care switch is off at the end

    def start(self):
        self.rpi_rf_gpiod.start()
        threading.Thread.start(self)

    def stop(self):
        self.is_on = False
        self.t_next_transmission = time.time() # transmit asap
        self.should_stop.set()
        self.rpi_rf_gpiod.stop()


def main():
    switch_in_fan = Switch(3017736, 3017732, verbose=True)
    switch_out_fan = Switch(2229972, 2229970, verbose=True)
    switch_heater = Switch(9707848, 9707844, verbose=True)

    switch_in_fan.start()
    switch_out_fan.start()
    switch_heater.start()
    time.sleep(10)

    switch_in_fan.on()
    switch_out_fan.on()
    switch_heater.on()
    time.sleep(10)

    switch_heater.off()
    switch_out_fan.off()
    switch_in_fan.off()
    time.sleep(10)

    switch_in_fan.on()
    switch_out_fan.on()
    switch_heater.on()
    time.sleep(130)

    switch_heater.stop()
    switch_out_fan.stop()
    switch_in_fan.stop()


if __name__ == '__main__':
    main()
