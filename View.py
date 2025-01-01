#!/usr/bin/env python3

"""
The view renders presentation of the model in a particular format.

Responsibilities:
- output on the LCD
- output on the switches

Architecture:
- implemented in a thread that tries to update the LCD content once a second
"""

import threading
import time
import sys
from datetime import datetime
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD2004 import Adafruit_CharLCD
from Leds import Leds
from Switch import Switch


PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.


class View(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.model = None
        self.should_stop = threading.Event() # create an unset event on init
        self.mcp = None
        self.lcd = None
        self.lcd_needs_recovery = False
        self.leds = Leds()
        self.leds.red(True)
        self.leds.green(True)
        self.switch = Switch(2229972, 2229970)
        # column numbers          01234567890123456789
        self.line1 = [c for c in "Bq nnnn DD.MON HH:MM"]
        self.line2 = [c for c in "E:xxx xx xx xx xx xx"]
        self.line3 = [c for c in "+tt.t aa.a% +tt.t XX"]
        self.line4 = [c for c in "+tt.t aa.a% +tt.t ie"]

    def backlight(self, on):
        self.mcp.output(3, on)    # switch the LCD backlight

    def init_display(self):
        """This is a stripped down __init__() function of Adafruit_LCD2004 to recover from LCD errors."""
        try:
            self.lcd.GPIO.setmode(self.lcd.GPIO.BCM) #GPIO=None use Raspi PIN in BCM mode
            self.lcd.GPIO.setup(self.lcd.pin_e, self.lcd.GPIO.OUT)
            self.lcd.GPIO.setup(self.lcd.pin_rs, self.lcd.GPIO.OUT)

            for pin in self.lcd.pins_db:
                self.lcd.GPIO.setup(pin, self.lcd.GPIO.OUT)

            self.lcd.write4bits(0x33)  # initialization
            self.lcd.write4bits(0x32)  # initialization
            self.lcd.write4bits(0x28)  # 2 line 5x7 matrix
            self.lcd.write4bits(0x0C)  # turn cursor off 0x0E to enable cursor
            self.lcd.write4bits(0x06)  # shift cursor right
            self.lcd.write4bits(self.lcd.LCD_ENTRYMODESET | self.lcd.displaymode)  # set the entry mode

            self.lcd.write4bits(self.lcd.LCD_CLEARDISPLAY)  # command to clear display
            self.lcd_needs_recovery = False
        except Exception as e:
            print(e)

    def update(self):
        if self.lcd_needs_recovery:
            self.init_display()

        if not self.lcd_needs_recovery:
            try:
                self.lcd.setCursor(0,0)  # set cursor position
                self.lcd.message(self.line1)
                self.lcd.setCursor(0,1)  # set cursor position
                self.lcd.message(self.line2)
                self.lcd.setCursor(0,2)  # set cursor position
                self.lcd.message(self.line3)
                self.lcd.setCursor(0,3)  # set cursor position
                self.lcd.message(self.line4)
            except Exception as e:
                print(e)
                self.lcd_needs_recovery = True

    def on_change_time(self):
        now = datetime.now()
        colon = ":" if (now.second & 1) else " "
        text = now.strftime("%d %b %H{}%M".format(colon))
        self.line1 = self.line1[0:8] + [c for c in text]

    def on_change_radon(self, Bq):
        if Bq is None:
            text = "----"
        else:
            text = "{: 4d}".format(int(Bq))
        for i in range(len(text)):
            self.line1[3+i] = text[i]

    def on_change_errors(self, errors):
        if errors:
            text = "E:"
            for key in ["ext", "NO", "SO", "SW", "NW", "Rn"]:
                if key in errors:
                    text += "{} ".format(key)
                else:
                    text += " " * (len(key) + 1)
        else:
            text = " " * 20
        for i in range(20):
            self.line2[i] = text[i]

    def on_change_temperature(self, temperature, line):
        if temperature is None:
            text = "-----"
        else:
            text = "{:+5.1f}".format(temperature)
        for i in range(len(text)):
            line[i] = text[i]

    def on_change_room_temperature(self, temperature):
        self.on_change_temperature(temperature, self.line2)

    def on_change_internal_temperature(self, temperature):
        self.on_change_temperature(temperature, self.line3)

    def on_change_external_temperature(self, temperature):
        self.on_change_temperature(temperature, self.line4)

    def on_change_humidity(self, humidity, line):
        if humidity is None:
            text = "----%"
        else:
            text = "{:4.1f}%".format(humidity)
        for i in range(len(text)):
            line[6+i] = text[i]

    def on_change_room_humidity(self, humidity):
        self.on_change_humidity(humidity, self.line2)

    def on_change_internal_humidity(self, humidity):
        self.on_change_humidity(humidity, self.line3)

    def on_change_external_humidity(self, humidity):
        self.on_change_humidity(humidity, self.line4)

    def on_change_dewpoint(self, dewpoint, line):
        if dewpoint is None:
            text = "-----"
        else:
            text = "{:+5.1f}".format(dewpoint)
        for i in range(len(text)):
            line[12+i] = text[i]

    def on_change_room_dewpoint(self, dewpoint):
        self.on_change_dewpoint(dewpoint, self.line2)

    def on_change_internal_dewpoint(self, dewpoint):
        self.on_change_dewpoint(dewpoint, self.line3)

    def on_change_external_dewpoint(self, dewpoint):
        self.on_change_dewpoint(dewpoint, self.line4)

    def on_change_location(self, key, line):
        if (type(key) == str) and (2 == len(key)):
            text = key
        else:
            text = "--"
        for i in range(len(text)):
            line[18+i] = text[i]

    def on_change_room_location(self, key):
        self.on_change_location(key, self.line2)

    def on_change_internal_location(self, key):
        self.on_change_location(key, self.line3)

    def on_change_switches(self, switches):
        self.line4[18] = ">" if switches["in_fan_on"] else "|"
        self.line4[19] = ">" if switches["out_fan_on"] else "|"
        self.leds.green(switches["out_fan_on"])
        self.leds.red(not switches["out_fan_on"])
        if switches["out_fan_on"]:
            self.switch.on()
        else:
            self.switch.off()

    def run(self):
        # Create PCF8574 GPIO adapter.
        try:
            self.mcp = PCF8574_GPIO(PCF8574_address)
        except:
            try:
                self.mcp = PCF8574_GPIO(PCF8574A_address)
            except:
                print ('I2C Address Error !')
                exit(1)

        # set the switch off
        self.switch.start()
        self.switch.off()

        # Create LCD, passing in MCP GPIO adapter.
        self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=self.mcp)
        self.lcd.begin(20,4)     # set number of LCD lines and columns
        self.lcd.clear()
        self.backlight(True)
        self.update()
        while not self.should_stop.is_set():
            t_wakeup = int(time.time() + 1)
            t_sleep = t_wakeup - time.time()
            if t_sleep < 0:
                t_sleep = 0  # avoid exception due to negative time
            time.sleep(t_sleep)
            self.on_change_time()
            if 0 == int(time.time()) % 5:
                if self.model:
                    self.model.on_time()
            self.update()

    def stop(self):
        self.should_stop.set()
        self.lcd.clear()
        self.backlight(False)
        self.leds.red(False)
        self.leds.green(False)
        self.switch.stop()


if __name__ == '__main__':
    view = View()
    try:
        view.start()
        while(True):
            view.on_change_radon(None) # Bq = None
            time.sleep(1)
            view.on_change_radon(123)  # valid
            time.sleep(1)
            view.on_change_radon(321)  # valid
            time.sleep(1)
            view.on_change_internal_temperature(+22.2) # valid
            time.sleep(1)
            view.on_change_internal_temperature(None) # None
            time.sleep(1)
            view.on_change_internal_temperature(-1.1) # valid
            time.sleep(1)
            view.on_change_external_temperature(+3.3) # valid
            time.sleep(1)
            view.on_change_external_temperature(None) # None
            time.sleep(1)
            view.on_change_external_temperature(-15.0) # valid
            time.sleep(1)
    except KeyboardInterrupt:
        view.stop()
