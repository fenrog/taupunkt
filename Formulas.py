#!/usr/bin/env python3

import numpy as np


def Myzelwachstum(relative_humidity, temperature):
    """
    relative_humidity in %
    temperature in °C
    v in mm/d
    https://passiv.de/downloads/05_kellerraeume.pdf
    Formel auf Seite 7
    """
    phi = relative_humidity / 100.0
    T = temperature
    v = 21 * (phi - 0.244 * np.exp(-0.12 * T) - 0.775)
    return v


def LIM(T):
    """
    Berechnung der maximalen reativen Luftfeuchtigkeit in Abhängigkeit von der Temperatur
    die nötig ist, damit gesundheitsschädliche Schimmelpilze wachsen.
    """
    for rH in range(0, 1001):
        v = Myzelwachstum(rH/10, T)
        if v >= 0.0:
            return (rH - 1) / 10
            break
    return None


lim_cache = {}
def get_lim(temperature):
    global lim_cache
    temperature = round(float(temperature), 1)
    if temperature not in lim_cache:
        lim = LIM(temperature)
        if lim is None:
            lim_cache[temperature] = lim
        else:
            lim_cache[temperature] = round(lim, 1)
    return lim_cache[temperature]


def Saettigungsdampfdruck(t_Celsius):
    if (t_Celsius >= 0):
        a = 7.5
        b = 237.3
    else:
        a = 7.6
        b = 240.7

    # Sättigungsdampfdruck in kPa
    sdd = 6.1078 * np.power(10, (a*t_Celsius)/(b+t_Celsius)) / 10
    return sdd


def Saettigungsmenge(t_Celsius, Psat):
    t_Kelvin = t_Celsius + 273.1
    roh = Psat / (461.5 * t_Kelvin) * 1000000 # in g/m³ Luft
    return roh


def Wassergehalt(t_Celsius, rH):
    return rH/100 * Saettigungsmenge(t_Celsius, Saettigungsdampfdruck(t_Celsius))


absolute_humidity_cache = {}
def get_absolute_humidity(temperature, rH):
    temperature = round(float(temperature), 1)
    rH = round(float(rH), 1)
    key = (temperature, rH)
    if key not in absolute_humidity_cache:
        absolute_humidity_cache[key] = round(Wassergehalt(temperature, rH), 1)
    return absolute_humidity_cache[key]


def main():
    print("LIM = {")
    for T in range(-10, 25):
        lim = get_lim(T)
        if lim is not None:
            print("    {}: {},".format(T, lim))
    print("}")

    print(get_absolute_humidity(10.6, 62.2), "g/m³")
    print(get_absolute_humidity(9.9, 61.5), "g/m³")

    print(get_absolute_humidity(7.7, 81.5), "g/m³")
    print(get_absolute_humidity(8.4, 74.5), "g/m³")


if __name__ == '__main__':
    main()
