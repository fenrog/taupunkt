# taupunkt
Taupunkt Lüftungssteuerung zur Kellerentfeuchtung mit Radonüberwachung

Ich entwickle das Programm angepasst auf meinen eigenen Keller. Eine Konfigurierbarkeit auf andere Situationen ist im aktuelen Zustand nicht gegeben.

Es handelt sich um einen unbeheizten Keller in einem ca. 120 Jahre alten Haus im Schwarzwald. Es gibt vier Kellerräume mit jeweils gut 20 m² und ein Treppenhaus mit etwas weniger als 20 m². Die Gesamtfläche liegt bei knapp 100 m². Das Haus liegt am Hang. Die Nordseite des Hauses liegt größtenteils unterirdisch, die Südseite hat einen ebenerdigen Ausgang vom Keller in den Garten.

Die Entwicklung und Inbetriebnahme findet inkrementel iterativ statt. In einem ersten Schritt sollen die Sensoren abgefragt und eine Lüftungsempfehlung über je eine rote und grüne LED erfolgen. Grün: lüften, rot: ncht lüften.

Falls sich das bewährt und eine weitere automatisierung gewünscht ist, kann im nächsten Schritt der Einbau und die Ansteuerung einer Lüftungsanlage erfolgen. Der Schalter soll über 433 MHz Funk rfolgen.

## Radon

Schwarzwald ist deshalb erwähnenswert, weil es hier eine erhöhte Radonkonzentration gibt. In meiner Gemeinde gibt es eine geschätzte Konzenration von 199 Bq/m³ in Wohnräumen. Der Bundesdurchscnitt liegt bei ca. 50 Bq/m³. [^1].

> Pro 100 Becquerel pro Kubikmeter Raumluft langjähriger Radon-Konzentration erhöht sich das Lungenkrebsrisiko um etwa 16 %. [^2]

> Als Maßstab für die Prüfung der Angemessenheit von Maßnahmen zum Schutz vor Radon dient gemäß Strahlenschutzgesetz ein Referenzwert von 300 Becquerel pro Kubikmeter. [^3]

> Allen Definitionen gemein ist, dass nicht erst gehandelt werden soll, wenn der Referenzwert überschritten wurde. Auch unterhalb des Referenzwertes können Maßnahmen sinnvoll sein. [^3]

[^1]: https://www.imis.bfs.de/geoportal/

[^2]: https://www.bfs.de/DE/themen/ion/umwelt/radon/karten/wohnraeume.html

[^3]: https://www.bfs.de/DE/themen/ion/umwelt/radon/regelungen/referenzwert.html

## Hardware

- 1 Raspberry Pi 3B V 1.2 mit 32 GB SD Karte
- 1 FREENOVE I2C LCD 2004 Module
- 1 RadonTec RadonEye RD200
- 5 DHT22 Temperatur und Luftfeuchtigkeitssensor (auf Platine mit Abschlusswiderstand und Kondensator) weil er mittels 1-Wire mehrere Meter vom Raspberry Pi entfernt in den Räumen platziert werden kann, im Gegensatz zu Sensoren die über I2C oder SPI angesteuert werden.
- 1 Breakout Board mit Schraubklemmen für Raspberry Pi 3B
- ausreichend J-Y(ST)Y 6x2x0,8 Telefonkabel bzw. KNX/EIB Busleitung
- ausreichend J-Y(ST)Y 2x2x0,8 Telefonkabel bzw. KNX/EIB Busleitung
- 1 TFA Dostman Schutzhülle für Außensender 98.1114
- 5 Abzweigdosen Aufputz 85x85x40 mm
- ausreichend Wagoklemmen 2-adrig
- 1 Lochrasterplatine
- 1 kwmobile 433 MHz Sender mit ASK Modulation
- 1 einkanaliger eMylo 433MHz RF Funk Fernbedienung Schalter mit ASK Modulation

Optional für zukünftige Erweiterungen
- aktive Lüftungsanlage
- evtl. Wärmetauscher
- Abschaltvorrichtung für die Lüftungsanlage

Q: Warum **Raspberry Pi 3B V 1.2 mit 32 GB SD Karte**? [^4]

A: Das hat mehrere Gründe
- Er hat LAN Anschluss und ich habe LAN aber kein WLAN im Keller.
- Er hat Bluetooth das für den **RadonTec RadonEye RD200** benötigt wird.
- Ein HDMI Monitor kann angeschlossen werden, falls das notwendig sein sollte. Z.B. weil der Zugriff ber SSH gerade nicht funktioniert oder weil lokal Messwerte visualisiert werden sollen.

[^4]: https://www.raspberrypi.com/products/raspberry-pi-3-model-b/

Q: Wozu **FREENOVE I2C LCD 2004 Module**

A: Laut Beschreibung und Rezensionen läuft es mit Raspberry Pi 3 während AZ-Delivery einen zwischengeschalteten Pegelwandler 3.3V / 5V haben möchte.

Q: Warum **RadonTec RadonEye RD200**? [^5]

A: Das hat mehrere Gründe
- Er ist über Bluetooth ansprechbar mit Python Modulen ansprechbar. [^6] [^7] [^8]
- Ein älteres Pytnon Modul, das vermutlich nicht mehr funktioniert. [^9]
- Er ist günstiger als **air-Q radon** der zudem WLAN voraussetzt, was ich nicht in Reichweite habe. [^10]
- Er hat ein Messintervall von 10 Minuten und eine gleitende Mittelwertbildung über eine Stunde. Damit gehört er zu den schnelleren Radon-Sensoren. [^11]
![Diagram Messwerte **air-Q radon sciense** vs **RadonEye RD200** vs **Airthings Wave Plus**](https://cdn.prod.website-files.com/5bd9feee2fb42232fe1d0196/672cbd9d2b75c236ee68f75d_comparison.png)

[^5]: http://radonftlab.com/radon-sensor-product/radon-detector/rd200/
[^6]: https://theprivatesmarthome.com/how-to/set-up-ecosense-radoneye-in-home-assistant-using-raspberry-pi-as-bluetooth-proxy/
[^7]: https://github.com/EtoTen/radonreader
[^8]: https://github.com/jdeath/rd200v2
[^9]: https://pypi.org/project/radonpy/
[^10]: https://www.air-q.com/messwerte/radon
[^11]: https://www.air-q.com/radon-messgeraete-vergleich

Q: Warum **DHT22**?

A: Das hat mehrere Gründe [^12]
- Zur Brechnung des Taupunkts wird die Temperatur und die relative Luftfeuchtigkeit benötigt. Luftdruck geht im Prinzip auch mit ein, kann aber vernachlässigt werden.
- Der Sensor muss mehrere Meter vom Raspberry Pi absetzbar sein. Damit fällt I2C, SPI und Analogspannung raus.
- **DHT22** hat gegenüber **DHT11** einen erweiterter Temperaturbereich der auch Minusgrade abdeckt und eine bessere Auflösung.

[^12]: https://randomnerdtutorials.com/dht11-vs-dht22-vs-lm35-vs-ds18b20-vs-bme280-vs-bmp180/

Q: Warum **Breakout Board mit Schraubklemmen für Raspberry Pi 3B**?

A: Um die Kabel zu den Sensoren auflegen zu können. Es gibt mehrere Hersteller solcher Boards. Ich habe eines mit LEDs gewählt. Das könnte sich noch als schädlich für die Kommunikation mit den Sensoren erweisen. Das wird sich zeigen.

Q: Warum **J-Y(ST)Y Xx2x0,8**?

A: Ich habe mich an diesem Artikel zur 1-Wire Busverlegung orientiert und das Fernmeldekabel ausgewählt. [^13]. 0,6 mm Kabeldurchmesser hätten bei den geringen Strömen des Sensors auch gereicht. Ich baue da lieber noch Reserve ein. Achtung: Es wird zunehmend Aluminimumkabel angeboten, dessen Oberfläche verkupfert ist. Diese Kabel sind zwar preiswerter als Kupferkabel aber gemäß mehrerer Berichte besteht das Risiko von Kabelbrüchen - sichtbar beim Abisolieren oder unsichtbar irgendwo im Kabelstrang. Bei der Adernbelegung des **J-Y(ST)Y 2x2x0,8** folge ich der Belegungstabelle aus [^13]: schwarz = GND, rot = +5V, gelb = Daten-Signal.

[^13]: https://wiki.fhem.de/wiki/1-Wire_Busverlegung

Q: Warum **TFA Dostman Schutzhülle für Außensender 98.1114**? [^14]

A: Der TFA Sender kommt zwar nicht zum Einsatz, aber der Einsatzzweck ist der gleiche. Der **DHT22** Temperatur und Feuchtesensor soll einerseits wettergeschützt im Außenbereich angebracht werden, darf aber dennoch nicht hermetisch von Umwelteinflüssen abgeschottet werden. Letztlich soll ja die Temperatur und die Luftfeuchtigkeit möglichst ohne Verfälschung und zeitliche Verzögerung ermittelt werden.

[^14]: https://www.tfa-dostmann.de/produkt/schutzhuelle-fuer-aussensender-98-1114/

Q: Warum **Abzweigdosen**?

A: Eine als Abzweigdose im Flur die mit **J-Y(ST)Y 6x2x0,8** vom **Raspberry Pi** aus angefahren wird (vier verdrillte Adernpaare aus Datensignal und GND, zwei Aderenpaare mit +5V). Von dort aus geht es weiter mit **J-Y(ST)Y 2x2x0,8** zu vier der **DHT22** Sensoren. Einer wird in der **TFA Dostman Schutzhülle** außen platziert, drei werden in **Abzweigdosen** innen platziert. Der fünfte Sensor wird nahe des **Raspberry Pi** direkt mit **J-Y(ST)Y 2x2x0,8** ebenfalls in einer **Abzweigdose** untergebracht. Die ungenutzten Kabeldurchführungen der **Abzweigdosen** werden geöffnet, damit ein Luftaustausch mit den Sensoren stattfnden kann.

Q: Wozu die **Lochrasterplatine**?

A: Sie wird mittels 2x20 poliger Buchsenleiste auf das **Breakout Board mit Schraubklemmen für Raspberry Pi 3B** gesteckt. Folgende Funktonen sind angeschlossen:

- rote und grüne LED als Lüftungsempfehlung
- 433 MHz Sender um den Funkschalter und damit die Lüftungsanlage zu schalten
- I2C LCD Anschluss

Q: Wozu **433 MHz Sender** und **433MHz Funk Fernbedienung Schalter**

A: Das hat mehrere Gründe
- Ich möchte den Raspberry Pi elektrisch "nicht in die Nähe" von 230 V lassen. Daher keine Lösung mit einem Relais sondern drahtlos.
- Ich habe kein WLAN im Keller, daher kommen WLAN-fähige Steckdosen nicht in Frage.

Q: Warum eine **aktive Lüftungsanlage**?

A: Um die Lüftung zu automatisieren und nicht selbst mitten in der Nacht, wenn es gerade günstige Bedingungen fürs Lüften gibt, die Fenster öffnen zu müssen.

Q: Warum ein **Wäremetauscher**?

A: An meinem Wohnort liegen die Durchschnittstemperaturn drei Monate im Jahr unter 0°C. An fünf Monaten werden typischerweise Tiefsttemperaturen unter 0°C erreicht. Damit der Keller und damit das Haus beim Lüften nicht zu sehr auskühlt soll die Wärme rückgewonnen werden.

Q: Warum eine **Abschaltvorrichtung für die Lüftungsanlage**?

A: Dieser Punkt steht zwar am Ende der Liste, ist aber für den sicheren Betrieb einer der wichtigsten. In einem der zu lüftenden Räume befindet sich eine raumluftabhängige Gastherme. Beim Lüften mittels Gebläse besteht prinzipiell die Gefahr dass im Keller ein Unterdruck entsteht. Falls das passiert, während die Gastherme gerade läuft, könnte der Druckausgleich über den Kamin erfolgen von dort Abgase in den Keller gesaugt werden. Dies gilt es aus Eigeninteresse zu vermeiden. Die Lösung muss abgestimmt sein auf die Art der Heizung. Der Hersteller meiner Therme hat eine eigene Lösung welche die Lüftung immer dann ausschaltet, wenn die Therme läuft. An diesem Punkt ist der Schornsteinfeger einzubinden. Er kann im Zweifel den Betrieb untersagen.

## Testaufbau

Zur Inbetriebnahme empfiehlt es sich, alle fünf DHT22, die beiden LEDs, das LCD, einen 433 MHz Sender und einen 433 MHz Empfänger auf einem Steckbrett aufzubauen und mitz dem Raspberry Pi zu verbinden.
Insbesondere die DHT22 haben relativ zueinander leichte Abweichungen die mittels Offset-Werten etwas aneinander angeglichen werden können. Damit man die Sensoren nach der Kalibrierung wieder erkennt und sie später auch an der richtigen Stelle platziert sollten diese gekennzeichnet werden. Bei mir mit `ext`, `NO`, `SO`, `SW`, `NW`.

# Raspberry Pi 3B einrichten

## SD-Karte vorbereiten

- Raspberry Pi Imager starten
- Raspberry Pi Modell = Raspberry Pi 3
- Betriebssystem = Raspberry Pi OS (other) -> Raspberry Pi OS Lite (64-bit)
    A port of Debian Bookworm with no desktop environment (Comatible with Raspberry Pi 3/4/400/5)
    Veröffentlicht 20024-11-19
- SD-Karte wählen und schreiben, idealerweise User, Passwort, WLAN und Sprache voreinstellen

## erster Start
- Tastatur, Monitor, Ethernet (oder temporär WLAN-Stick), Spannung anschließen

## Aktualisierungen laden
- Terminal starten (lokal oder über SSH z.B. mit Putty)
```
sudo apt update
sudo apt upgrade
```

## Projekt klonen

git installieren und konfigurieren
```
sudo apt install git
```

### nur lesender Zugriff

```
cd ~
git clone --recurse-submodules https://github.com/fenrog/taupunkt.git
```

### lesender und schreibender Zugriff

Existierende Schlüssel nach ~/.ssh kopieren und auf Zugriffsrechte der Dateien achten.
Evtl ist es hilfreich einen USB-Stick mit den Schlüsseln zu mounten. [^15]
[^15]: https://askubuntu.com/questions/37767/how-to-access-a-usb-flash-drive-from-the-terminal

```
lsblk  # in der Ausgabe schauen wie das USB-Laufwerk heist, bei mir ist das sda2
cd /media
sudo mkdir usb
sudo mount /dev/sda2 /media/usb
cd ~
mkdir .ssh
chmod -c 700 .ssh
cd .ssh
cp /media/usb/home/taupunkt/.ssh/id_ed25519 .
chmod -c 600 id_ed25519
cp /media/usb/home/taupunkt/.ssh/id_ed25519.pub .
chmod -c 644 id_ed25519.pub

# vor dem Abziehen des USB-Sticks:
umount /media/usb
```

git konfigurieren
```
git config --global init.defaultbranch "main"
git config --global user.name "John Doe"
git config --global user.email "johndoe@email.com"
```

klonen
```
cd ~
git clone --recurse-submodules git@github.com:fenrog/taupunkt.git
```

## Python vorbereiten
```
cd ~/taupunkt
python3 -m venv venv-taupunkt       # virtuelle Umgebung vorbereiten
source venv-taupunkt/bin/activate   # virtuelle Umgebung aktivieren
pip install --upgrade pip
pip install setuptools
pip install wheel
sudo apt install python3-dev
```

Alle weiteren Arbeiten mit Python setzen eine aktvierte virtuelle Umgebung voraus.

### Modul für DHT22 installieren [^15]

```
pip install adafruit-circuitpython-dht
sudo apt install libgpiod2
```

#### Inbetriebnahme Temperatur und Feuchtigkeitssensoren

Die DHT22 werden in der Variante mit 3 Pins genutzt.
`+` wird mit 3,3V verbunden
`-` wird mit GND verbunden
`out` wird je nach Sensor mit dem korrespondierenden GPIO verbunden:
- `ext`: GPIO_24
- `NO`: GPIO_23
- `SO`: GPIO_25
- `SW`: GPIO_26
- `NW`: GPIO_27
Abweichende Einstellungen sind in DHT22.json vorzunehmen.
TODO: Überprüfe ob die abweichenden Enstellungen aus DHT22.json in allen Scripts wirksam sind. Annahme: nein.

```
cd ~/taupunkt
python DHT22.py
```

Das Script "lernt" eine Minute lang die Offsets.
Falls die Sensoren alle am gleichen Platz und aklimatisiert sind, dann sollte DHT22.json geschrieben werden um die erlernten Offsets zu speichern.
Danach erfolgt zwei Minuten lang eine Demonstration der korrigierten Messwerte.

[^15]: https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup

### Modul für Taupunktberechnung

Zunächst hatte ich MetPy verwendet. [^16] Diese Berechnung benötigt jedoch ziemlich viel Rechenleistung. Daher stieg ich schließlich um auf einen Algorithmus des MakeMagazinDE den ich von C auf Python portiert habe. [^17] Daher das Modul numpy.

```
pip install numpy
```

#### Test Taupunktberechnung

```
cd ~/taupunkt
python Dewpoint.py
```

Der Test läuft fünf Minuten. Aus den bereits bekannten Werten der Temperatur und der relativen Luftfeuchtigkeit wird der Taupunkt berechnet.


[^16]: https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.dewpoint_from_relative_humidity.html#metpy.calc.dewpoint_from_relative_humidity
[^17]: https://github.com/MakeMagazinDE/Taupunktluefter/blob/main/Taupunkt_Lueftung/Taupunkt_Lueftung.ino Funktion `float taupunkt(float t, float r)`

### Modul für RadonTec RadonEye RD200 [^7]

#### radonreader
Die SW kam bereits mit dem Klonen von taupunkt, aber sie muss noch gebaut werden.
Hinweis: Der radonreader Hash ist `d889c754d713f9ccce3ec8aa23c0814d3894712e`

#### weiteres für den radonreader
Ich bin nicht interessiert an MQTT sondern am "low level" Auslesen des aktuellen Becquerel-Wertes. MQTT wird dennoch installiert um den Start der Software nicht zu verhindern.

```
sudo apt install libglib2.0-dev
pip install bluepy
pip install paho-mqtt
cd ~/taupunkt/venv-taupunkt/lib/python3.11/site-packages/bluepy # zum bluepy-helper wechseln
pwd  # absoluten Pfad des bluepy-helper ausgeben und kopieren für Nutzung weiter unten
cd ../../../../..
sudo setcap cap_net_raw+e /home/taupunkt/taupunkt/venv-taupunkt/lib/python3.11/site-packages/bluepy/bluepy-helper
sudo setcap cap_net_admin+eip /home/taupunkt/taupunkt/venv-taupunkt/lib/python3.11/site-packages/bluepy/bluepy-helper
```

Finde die MAC-Adresses des RadonTec RadonEye RD200. Auf der Unterseite des Geräts befindet sich ein Aufkleber mit Barcode und einer Nummer. Ergänze diese am Anfang um "FR:"
Der folgende Befehl sollte eine Reihe von Bluetooth Low Energy Geräten gefunden werden. Suche in der Ausgabe nach dem namen des Geräts. Die MAC Adresse steht am Anfang der Zeile.
In meinem Fall ist die Zeile `90:38:0C:58:96:D6 FR:HK01RE000381` und damit die MAC-Adresse `90:38:0C:58:96:D6`.
Danach kann man mit STRG+C abbrechen.

```
sudo hcitool lescan
```

Teste radon_reader.py mit der eben ermittelten MAC-Adresse.
Hninweiß: Falls auf dem Smartphone die RadonEye App installiert wurde, muss diese beendet werden. Das RadonEye RD200 kann nur eine BLE Verbindung halten und die ist freizuhalten für die Lüftungssteuerung.

```
cd ~/taupunkt/radonreader
python radon_reader.py -h
```

Drei Varianten der Abfrage: geschwätzig, normal, leise
```
python radon_reader.py -a 90:38:0C:58:96:D6 -t 1 -b -v
2024-12-17 15:14:38,678 - root - DEBUG - Sending payload (byte): b'P' To handle (int): 42
2024-12-17 15:14:38,940 - root - DEBUG - Radon Value Raw: b'P\n>\x00\x00\x00\x00\x00<\x00\n\x00'
2024-12-17 15:14:39,944 - root - INFO - Radon Value Bq/m^3: 62
2024-12-17 15:14:39,945 - root - INFO - Radon Value pCi/L: 1.6756756756756757
2024-12-17 [15:14:39] - 90:38:0C:58:96:D6 - Radon Value: 62.00 Bq/m^3

python radon_reader.py -a 90:38:0C:58:96:D6 -t 1 -b
2024-12-17 [15:14:44] - 90:38:0C:58:96:D6 - Radon Value: 62.00 Bq/m^3

python radon_reader.py -a 90:38:0C:58:96:D6 -t 1 -b -s
62.00
```

Test Lesen der Radonwerte
```
cd ~/taupunkt
python RD200.py
```

### Modul für LEDs [^18]

LEDs mit PWM (grün = Lüften, rot = zu)

```
sudo nano /boot/firmware/config.txt
```
ändere
```
dtparam=audio=on
```
zu
```
dtparam=audio=off
# PWM GPIO12 and GPIO13
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Danach
```
sudo reboot
# nach reboot
cd ~/taupunkt
source venv-taupunkt/bin/activate
lsmod | grep pwm
pip install rpi-hardware-pwm
```

#### Test LEDs

rote LED hängt an GPIO_12
grüne LED hängt an GPIO_13

```
cd ~/taupunkt
python Leds.py
```

Die rote und grüne LED sollten abwechselnd blinken. Zuerst ist die rote für eine Sekunde an, dann die grüne für eine Sekunde. Das wiederholt sich 10 mal.

Die Helligkeit der LEDs soll so getrimmt werden, dass sie in etwa gleich hell erscheinen.
Zwei Stellschrauben:
- der Vorwiederstand (bei mir 470 Ohm für grün und 1k für rot)
- der Duty-cycle (bei mir 100% - konstant an für grün und 10% für rot)

Mit einem Tester gemessene Spanungen über den LEDs
    - LED gn = 1,99V
    - LED rt = 1,90V

Berechnung der Vorwiderstände
    3,3V - 1,9V = 1,4V
    1,4V / 470 Ohm = 2,9 mA
    1,4V / 1 kOhm = 1,4 mA

[^18]: https://pypi.org/project/rpi-hardware-pwm/

### Module für den 433 MHz Sender (plus Empfänger zum Anlernen)

#### wiringpi [^19]
Die SW kam bereits mit dem Klonen von taupunkt, aber sie muss noch gebaut werden.
Hinweis: Der wiringpi tag ist `3.10`, der Hash ist `a0b52b3a40d5ffd604b1dee0a013f96fa629777d`
```
cd ~/taupunkt/wiringpi
./build
```

[^19]: https://tutorials-raspberrypi.de/wiringpi-installieren-pinbelegung/ 

#### 433Utils [^20]
Die SW kam bereits mit dem Klonen von taupunkt, aber sie muss noch gebaut werden.
Hinweis: Der 433Utils Hash ist `755cec14a7e16604f214beef2dcad8dbd09de324`
Hinweis: Der 433Utils/rc-switch Hash ist `c5645170be8cb3044f4a8ca8565bfd2d221ba182`
```
cd ~/taupunkt/433Utils/RPi_utils
```

edit RFSniffer.cpp and change `int PIN = 2;` to `int PIN = 1; // GPIO_18`
```
make all
```

#### Inbetriebnahme 433 MHz Sender

Zum Anlernen wird ein 433 MHz Empfänger benötigt.
wiringpi und 433Utils müssen gebaut sein.
Das Datensignal des Senders ist mit GPIO_17 verbunden.
Das Datensignal des Empfängers ist mit GPIO_18 verbunden.
Sender und Empfänger sind mit GND und +5V verbunden.

Mit dem RFSniffer werden die Codes für `an` und `aus` der Fernbedienung die zum 433 MHz Schalter abgehört.
Diese Codes werden dann benötigt um die Scripts bei bedarf anzupassen.
```
cd ~/taupunkt/433Utils/RPi_utils 
sudo ./RFSniffer
```
Bei mir sind die Codes für `an` = 2229972 und `aus` = 2229970.
Die erlernten Codes sind in Switch.py und in View.py einzutragen.

Zum Test den Schalter mit der original Fernbedieunung einschalten. Dann Switch.py starten. Der Schalter sollte unmittelbar ausgeschalet werden. Weiter geht es nach 10 Sekunden mit an, nach 10 Sekunden aus, nach 10 Sekunden an, nach 60 Sekunden an (automatische Wiederholung), nach 60 Sekunden an (automatische Wiederholung), nach 10 Sekunden aus.

```
cd ~/taupunkt
python Switch.py
```

[^20]: https://tutorials-raspberrypi.de/raspberry-pi-funksteckdosen-433-mhz-steuern/

### Modul für LCD [^21] [^22]

Die SW kam bereits mit dem Klonen von taupunkt, aber I2C muss noch aktiviert werden.
Hinweis: Der Freenove_LCD_Module Hash ist `4f03df728d3efd7975f0140cf97b3181e308ec87`

```
sudo raspi-config
```
-> 3 Interface Options, <Select>
-> I5 I2C, <Select>, <Yes>, <Ok>
-> <Finish>

```
sudo reboot
# nach reboot
cd ~/taupunkt
source venv-taupunkt/bin/activate
lsmod | grep i2c
sudo apt install i2c-tools
sudo i2cdetect -y 1
pip install smbus
```

#### Test Display

Test mit Freenove_LCD_Module. Es sollte die CPU Temperatur und die Uhrzeit angezeigt werden.
```
cd ~/taupunkt/Freenove_LCD_Module/Freenove_LCD_Module_for_Raspberry_Pi/Python/Python_Code/2.1_I2CLCD2004
python I2CLCD2004.py
```

Test mit dem Viewer. Es sollten Testausgaben der Taupunktsteuerung erscheinen.
```
cd ~/taupunkt
python View.py
```

[^21]: https://www.raspberrypi-spy.co.uk/2014/11/enabling-the-i2c-interface-on-the-raspberry-pi/ 
[^22]: https://github.com/Freenove/Freenove_LCD_Module

## Test Gesamtsoftware

Start mit Python
```
cd ~/taupunkt
python taupunkt.py
```

Start mit Shell Skript
```
cd ~/taupunkt
./taupunkt.sh
```

## automatischer Start [^23]

[^23]: https://tutorials-raspberrypi.de/raspberry-pi-autostart-programm-skript/

```
sudo nano /etc/init.d/taupunkt
```

Code des taupunkt Scripts:
```
#! /bin/sh
### BEGIN INIT INFO
# Provides: taupunkt
# Required-Start: $syslog
# Required-Stop: $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Taupunkt Steuerung
# Description:
### END INIT INFO

case "$1" in
    start)
        echo "taupunkt wird gestartet"
        # Starte Programm
        /home/taupunkt/taupunkt/taupunkt.sh
        ;;
    stop)
        echo "taupunkt wird beendet"
        # Beende Programm
        pkill -int -f 'taupunkt.py'
        ;;
    *)
        echo "Benutzt: /etc/init.d/taupunkt {start|stop}"
        exit 1
        ;;
esac

exit 0
```

Test:
```
sudo chmod a+x /etc/init.d/taupunkt
sudo /etc/init.d/taupunkt start
sudo /etc/init.d/taupunkt stop
```

Aktivierung für Autostart:
```
sudo update-rc.d taupunkt defaults
```

Deaktivierung des Autostart:
```
sudo update-rc.d -f taupunkt remove
```

# Offene Punkte

## Aufbau

### Elektrik

- Passt der Pi, Hat, LCD, LEDs, 433 MHz Sender zusammen in das Gehäuse oder braucht es ein größeres?
- Wo wird der Raspberry Pi angebracht?
- Wo wird die Verteilerdose angebracht?
- Wo laufen die Kabel zu den Sensoren und wie werden sie befestigt?
- Wo werden die Innensensoren platziert?
- Wo wird der Außensensor platziert?
    -> von außen gesehen links neben der Eingangstür, im Windschatten in der Ecke zwischen Hauswand und Wand am Eingangsbereich, regengeschützt unter dem Vordach
- IUM für Bosch/Junkers Gastherme
- Entkoppelung der Stromkreise von IUM und Lüftung (IUM läuft über Therme mit Sicherung im EG, Lüftung läuft über Sicherung im OG)
- 433 MHz Schalter hinter IUM und vor Lüftung

### Lüftung

- Wärmetauscher
    - wo anbringen
    - wie dimensionieren
- Lüfter
    - wo anbringen
    - wie dimensionieren
- Schläuche / Rohre für Luftführung
    - wo anbringen
    - wie dimensionieren
- Zuluft / Abluft
    - wo, wie
- Kernlochbohrungen in der Wand oder Löcher in den Fenstern?

## Software

- automatischer Neustart falls es nicht mehr läuft

- Langzeit Messwerterfassung
    - 5 x Temperatur + relative Luftfeuchtigkeit + Taupunkt; minütlich 5 x 3 Werte
        -> 15 Werte / min
        -> 900 Werte / h
        -> 21600 Werte / Tag
        -> 7884000 / Jahr
    - 1 x Radon; en Werte alle 10 Minuten
        -> 6 Werte / h
    - 1 * Boolean für lüften / nicht lüften

- Grafana mit Webinterface zur Visualisierung der Daten
