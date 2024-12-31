#!/usr/bin/python3

"""
The model is responsible for managing the data of the application. It receives user input from the controller.
Collects the environmental data and calculates the fan swicth settings.

Optional in future:
- The in-fan-on information from the differential preassure monitor (low preasure pre warning)
- The out-fan-off information from the differential preassure monitor (immeidate low preasure fan off)

Responsibility:
- Calculate the fan power switches

- calculate the fan settings on change of the radon value with hysteresis between RADON_BQ_FAN_ON and RADON_BQ_FAN_OFF
-- if no radon value is available in case of errors, ventilation is not requested
-- if the radon value rises above RADON_BQ_FAN_ON, ventilation is requested
-- if the radon value falls below RADON_BQ_FAN_OFF, ventilation is no longer requested

- on update of the dewpoints
-- for the group of the internal sensors select the one with the minimum dewpoint, use a resolution of one digit after the decimal point
-- for the external sensor collect temperature, humidity, dewpoint with a resolution of one digit after the decimal point

- calculate the fan settings on change of the internal humidity with hysteresis between HUMIDITY_FAN_ON and HUMIDITY_FAN_OFF
-- if no internal humidity is available in case of errors, ventilation is not requested
-- if the internal humidity rises above HUMIDITY_FAN_ON, ventilation is requested
-- if the internal humidity falls below HUMIDITY_FAN_OFF, ventilation is no longer requested

- calculate the fan settings on change of the dew points with hysteresis between DEWPOINT_FAN_ON and DEWPOINT_FAN_OFF
-- if not both internal and external dewpoints are available in case of errors, ventilation is disallowed
-- the dew point difference is calculated as (internal dew point - external dew point)
-- if the dew point difference rises above DEWPOINT_FAN_ON, ventilation is allowed
-- if the dew point difference falls below DEWPOINT_FAN_OFF, ventilation is disallowed

- calculate the fan settings on change of the internal temperature with lower limit of MIN_INTERNAL_TEMP
-- if no internal temperature is available in case of errors, ventilation is disallowed
-- if the internal temperature falls below MIN_INTERNAL_TEMP, ventilation is disallowed

- calculate the fan settings on change of the external temperature with lower limit of MIN_EXTERNAL_TEMP
-- if no external temperature is available in case of errors, ventilation is disallowed
-- if the external temperature falls below MIN_EXTERNAL_TEMP, ventilation is disallowed

Optional in future:
- controll the out-fan and in-fan power switches independently
- calculate the fan settings on change of the out-fan-off from the differential preassure monitor
-- if out-fan-off is requested, both in-fan and out-fan are turned off
-- in-fan off may be overruled by in-fan-reuest
- calculate the fan settings on change of the in-fan-on from the differential preassure monitor
-- if in-fan-on is requested, the in-fan is turned on regardles of any other ventilation result
   in order to prevent exhaust gas to be pulled in through the chimney
"""

import time


RADON_BQ_FAN_ON = 100  # if the Radon Bq value is >= this limit, the ventilation shall start (if other conditons allow)
RADON_BQ_FAN_OFF = 75  # if the Radon Bq value is <= this limit, the ventilation shall stop

HUMIDITY_FAN_ON =  65  # if the relative humidity is >= this limit, the ventilation shall start (if other conditons allow)
HUMIDITY_FAN_OFF = 55  # if the relative humidity is <= this limit, the ventilation shall stop

DEWPOINT_FAN_ON =   5  # if the dewpoint difference is >= this limit, the ventilation may start (if other conditons allow)
DEWPOINT_FAN_OFF =  3  # if the dewpoint difference is <= this limit, the ventilation has to stop

MIN_INTERNAL_TEMP = 10   # below this temperature no ventilation is allowed
MIN_EXTERNAL_TEMP = -10  # below this temperature no ventilation is allowed


class Model():
    def __init__(self, view, verbose=False):
        self.verbose = verbose
        self.view = view
        self.view.model = self
        self.radon = {"Bq": None, "error": None}
        self.dewpoints = {
            "ext": {"temperature": None, "humidity": None, "dewpoint": None, "error": None},
            "NO": {"temperature": None, "humidity": None, "dewpoint": None, "error": None},
            "SO": {"temperature": None, "humidity": None, "dewpoint": None, "error": None},
            "SW": {"temperature": None, "humidity": None, "dewpoint": None, "error": None},
            "NW": {"temperature": None, "humidity": None, "dewpoint": None, "error": None},
        }
        self.internal = {"temperature": None, "humidity": None, "dewpoint": None, "error": None, "key": None}
        self.external = {"temperature": None, "humidity": None, "dewpoint": None, "error": None}
        self.communication_errors = ["ext", "NO", "SO", "SW", "NW"]
        self.time_key_index = -1
        self.ventilation = {
            "radon_request": None,
            "humidity_request": None,
            "dewpoint_granted": None,
            "internal_temp_granted": None,
            "external_temp_granted": None,
            "out_fan_granted": True,  # future improvement to read the sensors, but switch allready foreseen
            "in_fan_request": False,  # future improvement to read the sensors, but switch allready foreseen
        }
        self.switches = {
            "out_fan_on": None,
            "in_fan_on": None,
        }

    def on_time(self):
        if (not self.communication_errors) and (not self.radon["error"]):
            # there is no error present, show temperature/humidity/dewpoint of the non active internal room
            keys = ["NO", "SO", "SW", "NW"]
            self.time_key_index = (self.time_key_index + 1) % len(keys)
            key = keys[self.time_key_index]
            if key == self.internal["key"]:
                self.time_key_index = (self.time_key_index + 1) % len(keys)
                key = keys[self.time_key_index]

            self.view.on_change_room_temperature(self.dewpoints[key]["temperature"])
            self.view.on_change_room_humidity(self.dewpoints[key]["humidity"])
            self.view.on_change_room_dewpoint(self.dewpoints[key]["dewpoint"])
            self.view.on_change_room_location(key)

    def on_change_radon(self, Bq, error):
        print(int(time.time()), "on_change_radon({}, {})".format(Bq, error))
        if self.radon["Bq"] != Bq:
            self.radon["Bq"] = Bq
            self.view.on_change_radon(Bq)
        if self.radon["error"] != error:
            self.radon["error"] = error
            self.on_change_errors()

        radon_request = self.ventilation["radon_request"]  # default for hyteresis
        if error:                                          # error handling
            radon_request = False
        elif Bq >= RADON_BQ_FAN_ON:                        # hyteresis high
            radon_request = True
        elif Bq <= RADON_BQ_FAN_OFF:                       # hyteresis low
            radon_request = False
        if self.ventilation["radon_request"] != radon_request:
            self.ventilation["radon_request"] = radon_request
            self.on_change_ventilation()

    def on_update_dewpoints(self, averaged):
        print(int(time.time()), "on_change_dewpoints()")
        self.dewpoints = averaged

        # select internal minimum dewpoint
        min_key = None
        min_dewpoint = None
        communication_errors = []
        for key in averaged:
            print("{:3s} {}".format(key, averaged[key]))
            if averaged[key]["dewpoint"] is not None:
               if "ext" != key:
                    if min_key is None:
                        min_key = key
                        min_dewpoint = averaged[key]["dewpoint"]
                    elif min_dewpoint > averaged[key]["dewpoint"]:
                        min_key = key
                        min_dewpoint = averaged[key]["dewpoint"]

            else:
                communication_errors.append(key)
        if (min_key):
            internal = {
                "temperature": averaged[min_key]["temperature"],
                "humidity": averaged[min_key]["humidity"],
                "dewpoint": averaged[min_key]["dewpoint"],
                "error": False,
                "key": min_key,
            }
        else:
            internal = {
                "temperature": None,
                "humidity": None,
                "dewpoint": None,
                "error": None,
                "key": None,
            }

        # collect external data
        external = {
            "temperature": averaged["ext"]["temperature"],
            "humidity": averaged["ext"]["humidity"],
            "dewpoint": averaged["ext"]["dewpoint"],
            "error": averaged["ext"]["error"],
        }

        # callback if data changed
        if (self.internal != internal) or (self.external != external):
            diff_internal = []
            diff_external = []
            for key in internal:
                if (key not in self.internal) or (self.internal[key] != internal[key]):
                    diff_internal.append(key)
            for key in external:
                if (key not in self.external) or (self.external[key] != external[key]):
                    diff_external.append(key)
            self.internal = internal
            self.external = external
            self.on_change(diff_internal, diff_external)
        if self.communication_errors != communication_errors:
            self.communication_errors = communication_errors
            self.on_change_communication_errors()

    def on_change(self, diff_internal, diff_external):
        print(int(time.time()), "on_change()")
        if self.verbose:
            if diff_internal:
                print("internal", self.internal, diff_internal)
            if diff_external:
                print("external", self.external, diff_external)

        # ventilation and view relevant changes
        ventilation_is_changed = False
        if "humidity" in diff_internal:
            ventilation_is_changed |= self.on_change_internal_humidity(self.internal["humidity"])
        if ("dewpoint" in diff_internal) or ("dewpoint" in diff_external):
            ventilation_is_changed |= self.on_change_dewpoint(self.internal["dewpoint"], self.external["dewpoint"])
        if "temperature" in diff_internal:
            ventilation_is_changed |= self.on_change_internal_temperature(self.internal["temperature"])
        if "temperature" in diff_external:
            ventilation_is_changed |= self.on_change_external_temperature(self.external["temperature"])
        if ventilation_is_changed:
            self.on_change_ventilation()

        # view only relevant changes
        if "key" in diff_internal:
            self.on_change_internal_location(self.internal["key"])
        if "humidity" in diff_external:
            self.on_change_external_humidity(self.external["humidity"])

    def on_change_internal_humidity(self, internal_humidity):
        print(int(time.time()), "on_change_internal_humidity()")
        self.view.on_change_internal_humidity(internal_humidity)
        humidity_request = self.ventilation["humidity_request"]         # default for hyteresis
        if internal_humidity is None:                                   # error handling
            humidity_request = False
        elif internal_humidity >= HUMIDITY_FAN_ON:                      # hyteresis high
            humidity_request = True
        elif internal_humidity <= HUMIDITY_FAN_OFF:                     # hyteresis low
            humidity_request = False

        ventilation_is_changed = False
        if self.ventilation["humidity_request"] != humidity_request:
            self.ventilation["humidity_request"] = humidity_request
            ventilation_is_changed = True
        return ventilation_is_changed

    def on_change_dewpoint(self, internal_dewpoint, external_dewpoint):
        print(int(time.time()), "on_change_dewpoint()")
        self.view.on_change_internal_dewpoint(internal_dewpoint)
        self.view.on_change_external_dewpoint(external_dewpoint)
        dewpoint_granted = self.ventilation["dewpoint_granted"]         # default for hyteresis
        if (internal_dewpoint is None) or (external_dewpoint is None):  # error handling
            dewpoint_granted = False
        else:
            diff_dewpoint = internal_dewpoint - external_dewpoint
            if diff_dewpoint >= DEWPOINT_FAN_ON:                        # hyteresis high
                dewpoint_granted = True
            if diff_dewpoint <= DEWPOINT_FAN_OFF:                       # hyteresis low
                dewpoint_granted = False

        ventilation_is_changed = False
        if self.ventilation["dewpoint_granted"] != dewpoint_granted:
            self.ventilation["dewpoint_granted"] = dewpoint_granted
            ventilation_is_changed = True
        return ventilation_is_changed

    def on_change_internal_temperature(self, internal_temperature):
        print(int(time.time()), "on_change_internal_temperature()")
        self.view.on_change_internal_temperature(internal_temperature)
        internal_temp_granted = False                   # default for boolean
        if internal_temperature is None:                # error handling
            internal_temp_granted = False
        elif internal_temperature < MIN_INTERNAL_TEMP:  # bad case
            internal_temp_granted = False
        else:
            internal_temp_granted = True                # good case

        ventilation_is_changed = False
        if self.ventilation["internal_temp_granted"] != internal_temp_granted:
            self.ventilation["internal_temp_granted"] = internal_temp_granted
            ventilation_is_changed = True
        return ventilation_is_changed

    def on_change_external_temperature(self, external_temperature):
        print(int(time.time()), "on_change_external_temperature()")
        self.view.on_change_external_temperature(external_temperature)
        external_temp_granted = False                   # default for boolean
        if external_temperature is None:                # error handling
            external_temp_granted = False
        elif external_temperature < MIN_EXTERNAL_TEMP:  # bad case
            external_temp_granted = False
        else:
            external_temp_granted = True                # good case

        ventilation_is_changed = False
        if self.ventilation["external_temp_granted"] != external_temp_granted:
            self.ventilation["external_temp_granted"] = external_temp_granted
            ventilation_is_changed = True
        return ventilation_is_changed

    def on_change_ventilation(self):
        print(int(time.time()), "on_change_ventilation()")
        if self.ventilation["radon_request"] or self.ventilation["humidity_request"]:
            # request by at least one of radon or humidity
            if self.ventilation["dewpoint_granted"] \
            and self.ventilation["internal_temp_granted"] \
            and self.ventilation["external_temp_granted"]:
                # dewpoint difference, internal and exteranl temperatures are above the limits
                out_fan_on = True
                in_fan_on = True
            else:
                # at minimum one of dewpoint difference, internal or exteranl temperatures is below the limits
                out_fan_on = False
                in_fan_on = False
        else:
            # no request by neitehr radon nor humidity
            out_fan_on = False
            in_fan_on = False

        # if the differential preassure monitor signals out_fan_off, both fans are off (if not overruled by "in_fan_request")
        if not self.ventilation["out_fan_granted"]:
            out_fan_on = False
            in_fan_on = False

        # prevent danger of pulling exhaust gasses through the chimney, in fan request overrules everything
        if self.ventilation["in_fan_request"]:
            in_fan_on = True

        # calculate changes for power switch settings
        switches_changed = False
        if self.switches["out_fan_on"] != out_fan_on:
            self.switches["out_fan_on"] = out_fan_on
            switches_changed = True
        if self.switches["in_fan_on"] != in_fan_on:
            self.switches["in_fan_on"] = in_fan_on
            switches_changed = True
        if self.verbose:
            print(self.ventilation)
            print(self.switches)
        if switches_changed:
            self.view.on_change_switches(self.switches)

    def on_change_internal_location(self, location):
        print(int(time.time()), "on_change_external_humidity()")
        self.view.on_change_internal_location(location)

    def on_change_external_humidity(self, external_humidity):
        print(int(time.time()), "on_change_external_humidity()")
        self.view.on_change_external_humidity(external_humidity)

    def on_change_communication_errors(self):
        print(int(time.time()), "on_change_communication_errors()")
        if self.verbose:
            if self.communication_errors:
                print("communication_errors", self.communication_errors)
        self.on_change_errors()

    def on_change_errors(self):
        print(int(time.time()), "on_change_errors()")
        if self.radon["error"]:
            self.view.on_change_errors(self.communication_errors + ["Rn"])
        else:
            self.view.on_change_errors(self.communication_errors)

def main():
    model = Model(verbose=True)
    # TODO: demonstrate all the functions


if __name__ == '__main__':
    main()
