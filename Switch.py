import threading
import time

VARIANT_CODESEND = 1      # codesend uses GPIO17; ./433Utils/RPi_utils/codesend.cpp has to be edited and compiled to change
VARIANT_RPI_RF_SEND = 2   # uses GPIO as configured
VARIANT_RPI_RF_GPIOD = 3  # uses GPIO as configured
VARIANT = VARIANT_RPI_RF_GPIOD

if VARIANT in [VARIANT_CODESEND, VARIANT_RPI_RF_SEND]:
    import subprocess
else:
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

class Switch(threading.Thread):
    def __init__(self, on_code, off_code, verbose=False):
        threading.Thread.__init__(self)
        self.on_code = on_code
        self.off_code = off_code
        self.verbose = verbose
        self.is_on = False
        self.should_stop = threading.Event() # create an unset event on init
        if VARIANT == VARIANT_RPI_RF_GPIOD:
            self.chip = gpiod.Chip("gpiochip0")
            self.gpio = self.chip.get_line(GPIO)
            self.rfdevice = RFDevice(self.gpio)
            self.rfdevice.tx_repeat = 4
            self.gpio.request(consumer="rpi-rf_send", type=gpiod.LINE_REQ_DIR_OUT)

    def on(self):
        if not self.is_on:
            self.is_on = True
            self.t_next_transmission = time.time() # transmit asap
            if self.verbose:
                print(int(self.t_next_transmission), "on()")

    def off(self):
        if self.is_on:
            self.is_on = False
            self.t_next_transmission = time.time() # transmit asap
            if self.verbose:
                print(int(self.t_next_transmission), "off()")

    def transmit(self):
        try:
            if VARIANT == VARIANT_CODESEND:
                command = r"./433Utils/RPi_utils/codesend {}".format(self.on_code if self.is_on else self.off_code).split()
                result = subprocess.run(command, stdout=subprocess.PIPE)
                if self.verbose:
                    print(int(time.time()), result.stdout)

            elif VARIANT == VARIANT_RPI_RF_SEND:
                command = r"rpi-rf_send -g {} {}".format(GPIO, self.on_code if self.is_on else self.off_code).split()
                result = subprocess.run(command, stdout=subprocess.PIPE)
                if self.verbose:
                    print(int(time.time()), result.stdout)

            elif VARIANT == VARIANT_RPI_RF_GPIOD:
                self.rfdevice.tx_code(self.on_code if self.is_on else self.off_code, 1, 350, 24)
                if self.verbose:
                    print(int(time.time()), self.on_code if self.is_on else self.off_code)
        except Exception as e:
            if VARIANT in [VARIANT_CODESEND, VARIANT_RPI_RF_SEND]:
                if result is not None:
                    print(result)
            print(e)

    def run(self):
        self.t_next_transmission = time.time()
        while not self.should_stop.is_set():
            if time.time() >= self.t_next_transmission:
                self.t_next_transmission += 60  # next desired transmission in 60 seconds
                self.transmit()

            t_sleep = self.t_next_transmission - time.time()
            if t_sleep > 1:
                t_sleep = 1  # do not wait longer than one second in order to stop asap
            if t_sleep < 0:
               t_sleep = 0  # avoid exception due to negative time
            time.sleep(t_sleep)
        self.transmit() # take care swicth is off at the end

    def stop(self):
        self.is_on = False
        self.t_next_transmission = time.time() # transmit asap
        self.should_stop.set()


def main():
    switch = Switch(2229972, 2229970, verbose=True)
    switch.start()
    time.sleep(10)
    switch.on()
    time.sleep(10)
    switch.off()
    time.sleep(10)
    switch.on()
    time.sleep(130)
    switch.stop()


if __name__ == '__main__':
    main()
