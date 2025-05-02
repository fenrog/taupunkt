import time
from rpi_hardware_pwm import HardwarePWM


"""
sudo nano /boot/firmware/config.txt
disable audio: `dtparam=audio=off`
enable PWM:
```
# PWM GPIO12 and GPIO13
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

red LED is connected to GPIO12; red needs little currecnt, thus 1k Ohm to GND; PWM 10%
green LED is connected to GPIO13; green needs more current, thus 470 Ohm  to GND; PWM 100%
"""

class Leds():
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.rd_status = None
        self.gn_status = None
        self.rd = HardwarePWM(pwm_channel=0, hz=1000, chip=0)
        self.gn = HardwarePWM(pwm_channel=1, hz=1000, chip=0)

    def red(self, on):
        if self.rd_status != on:
            self.rd_status = on
            if self.verbose:
                print("LED red {}".format("on" if on else "off"))
            if on:
                self.rd.start(10)
            else:
                self.rd.stop()

    def green(self, on):
        if self.gn_status != on:
            self.gn_status = on
            if self.verbose:
                print("LED green {}".format("on" if on else "off"))
            if on:
                self.gn.start(100)
            else:
                self.gn.stop()


def main():
    leds = Leds()
    for i in range(10):
        leds.red(True)
        time.sleep(1)
        leds.red(False)
        leds.green(True)
        time.sleep(1)
        leds.green(False)


if __name__ == '__main__':
    main()

