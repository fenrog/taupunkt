#!/usr/bin/env python3

"""
The view renders presentation of the model in a particular format.

Responsibilities:
- output on the LCD
- output on the switches

Architecture:
- implemented in a thread that tries to update the LCD content once a second
"""

VARIANT_ADAFRUIT = 1
VARIANT_RPI_GPIO_I2C_LCD = 2
VARIANT = VARIANT_RPI_GPIO_I2C_LCD


import threading
import time
import sys
from datetime import datetime
if VARIANT == VARIANT_ADAFRUIT:
    from PCF8574 import PCF8574_GPIO
    from Adafruit_LCD2004 import Adafruit_CharLCD
elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
    from RPi_GPIO_i2c_LCD import lcd
from Leds import Leds
from Switch import Switch


PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.


class View(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.model = None
        self.should_stop = threading.Event() # create an unset event on init
        if VARIANT == VARIANT_ADAFRUIT:
            self.mcp = None
            self.lcd = None
            self.lcd_needs_recovery = False
        elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
            self.lcd = None
        self.leds = Leds()
        self.leds.red(True)
        self.leds.green(True)
        self.switch_in_fan = Switch(3017736, 3017732)
        self.switch_out_fan = Switch(2229972, 2229970)
        self.switch_heater = Switch(9707848, 9707844)
        # column numbers          01234567890123456789
        self.line1 = [c for c in "Bq nnnn DD MON HH:MM"]
        self.line2 = [c for c in "+tt.t aa.a% +tt.t XX"]
        self.line3 = [c for c in "+tt.t aa.a% +tt.t XX"]
        self.line4 = [c for c in "+tt.t aa.a% +tt.t <>"]
        self.air_stream_on = False
        self.communication_error = True
        self.communication_error_led_toggle = True

    def backlight(self, on):
        if VARIANT == VARIANT_ADAFRUIT:
            if self.mcp is not None:
                self.mcp.output(3, on)    # switch the LCD backlight
        elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
            if self.lcd is not None:
                self.lcd.backlight("on" if on else "off")

    def init_display(self):
        """This is a stripped down __init__() function of Adafruit_LCD2004 to recover from LCD errors."""
        if VARIANT == VARIANT_ADAFRUIT:
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
        elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
            self.lcd.clear()

    def update(self):
        for i in [5, 11, 17]:
            self.line2[i] = " "
            self.line3[i] = " "
            self.line4[i] = " "

        if VARIANT == VARIANT_ADAFRUIT:
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
        elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
            try:
                self.lcd.set("".join(c for c in self.line1), 1)
                self.lcd.set("".join(c for c in self.line2), 2)
                self.lcd.set("".join(c for c in self.line3), 3)
                self.lcd.set("".join(c for c in self.line4), 4)
            except Exception as e:
                print(e)

        self.leds.green(self.air_stream_on)
        if not self.communication_error:
            self.leds.red(not self.air_stream_on)
        else:
            self.leds.red(self.communication_error_led_toggle)

    def on_change_time(self):
        now = datetime.now()
        colon = ":" if (now.second & 1) else " "
        text = now.strftime("%d %b %H{}%M".format(colon))
        self.line1 = self.line1[0:8] + [c for c in text]
        if self.communication_error:
            self.communication_error_led_toggle = not self.communication_error_led_toggle

    def on_change_radon(self, Bq):
        if Bq is None:
            text = "----"
        else:
            text = "{: 4d}".format(int(Bq))
        for i in range(len(text)):
            self.line1[3+i] = text[i]

    def on_change_temperature(self, temperature, line, offset=0):
        if temperature is None:
            text = "-----"
        else:
            text = "{:+5.1f}".format(temperature)
        for i in range(len(text)):
            line[i+offset] = text[i]

    def on_change_humidity(self, humidity, line):
        if humidity is None:
            text = "----%"
        else:
            text = "{:4.1f}%".format(humidity)
        for i in range(len(text)):
            line[6+i] = text[i]

    def on_change_dewpoint(self, dewpoint, line):
        self.on_change_temperature(dewpoint, line, offset=12)

    def on_change_location(self, key, line):
        if (type(key) == str) and (2 == len(key)):
            text = key
        else:
            text = "--"
        for i in range(len(text)):
            line[18+i] = text[i]

    def on_change_north(self, temperature, humidity, dewpoint, location):
        self.on_change_temperature(temperature, self.line2)
        self.on_change_humidity(humidity, self.line2)
        self.on_change_dewpoint(dewpoint, self.line2)
        self.on_change_location(location, self.line2)

    def on_change_south(self, temperature, humidity, dewpoint, location):
        self.on_change_temperature(temperature, self.line3)
        self.on_change_humidity(humidity, self.line3)
        self.on_change_dewpoint(dewpoint, self.line3)
        self.on_change_location(location, self.line3)

    def on_change_external_temperature(self, temperature):
        self.on_change_temperature(temperature, self.line4)

    def on_change_external_humidity(self, humidity):
        self.on_change_humidity(humidity, self.line4)

    def on_change_external_dewpoint(self, dewpoint):
        self.on_change_dewpoint(dewpoint, self.line4)

    def on_change_switches(self, switches):
        self.line4[17] = "*" if switches["heater_on"] else " "
        self.line4[18] = "<" if switches["in_fan_on"] else "|"
        self.line4[19] = ">" if switches["out_fan_on"] else "|"

        self.air_stream_on = switches["in_fan_on"] or switches["out_fan_on"]

        if switches["in_fan_on"]:
            self.switch_in_fan.on()
        else:
            self.switch_in_fan.off()
        if switches["out_fan_on"]:
            self.switch_out_fan.on()
        else:
            self.switch_out_fan.off()
        if switches["heater_on"]:
            self.switch_heater.on()
        else:
            self.switch_heater.off()

    def on_change_communication_error(self, status):
        self.communication_error = status
        if self.communication_error:
            self.communication_error_led_toggle = True

    def run(self):
        # switch the out fan off
        self.switch_out_fan.start()
        self.switch_out_fan.off()

        # Create PCF8574 GPIO adapter.
        if VARIANT == VARIANT_ADAFRUIT:
            try:
                self.mcp = PCF8574_GPIO(PCF8574_address)
            except:
                try:
                    self.mcp = PCF8574_GPIO(PCF8574A_address)
                except:
                    print ('I2C Address Error !')
                    exit(1)

        # Create LCD, passing in MCP GPIO adapter.
        if VARIANT == VARIANT_ADAFRUIT:
            self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=self.mcp)
            self.backlight(True)
            self.lcd.begin(20,4)     # set number of LCD lines and columns
            self.lcd.clear()
            self.update()
        elif VARIANT == VARIANT_RPI_GPIO_I2C_LCD:
            self.lcd = lcd.HD44780(0x27)
            self.backlight(True)
            self.lcd.clear()
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
        if self.lcd is not None:
            self.lcd.clear()
        self.backlight(False)
        self.leds.red(False)
        self.leds.green(False)
        self.switch_out_fan.stop()


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
            view.on_change_north(+22.2, 22, -2.2, "NW") # valid
            view.on_change_south(-33, 33, -3.3, "SW") # None
            time.sleep(1)
            view.on_change_north(None, None, None, "NO") # None
            view.on_change_south(None, None, None, "SO") # valid
            time.sleep(1)
            view.on_change_external_temperature(+44.4) # valid
            view.on_change_external_humidity(44) # valid
            view.on_change_external_dewpoint(-4.4) # valid
            time.sleep(1)
            view.on_change_external_temperature(None) # None
            view.on_change_external_humidity(None) # valid
            view.on_change_external_dewpoint(None) # valid
            time.sleep(1)
    except KeyboardInterrupt:
        view.stop()
