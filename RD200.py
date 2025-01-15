#!/usr/bin/python3

"""
One RadonEye RD200 sensor is located in the celar room "SO". It can be queried with Bluetooth Low Energy (BLE).
The RD200 has an update frequency of 10 minutes and a moving average of 60 minutes.
The first value can be obtained 10 minutes after power on.

Responsibility:
- cyclicylly read the sensor every minute with an external application (in order to detect an update of the data with a maximum delay of 1 minute)
- the return value shall be converted into a float number, if not possible, an error shall be set
- on change of either the Bq value or the error or a timeout of 10 minuts inform the client with a callback

Architecture:
- external application is executed as subprocess
- the return value of the application is expected to be a single float value for the number of Bq, but in case of errors it can also be an error string
- the external application can stall quite a while i.e. because of device failures, bad connection, or another device connected
- For ths reason a timer cannot be used. We sahll avoid to start multiple processes in parallel.
"""

import subprocess
import threading
import time

MAC_ADDRESS = "90:38:0C:58:96:D6"
TYPE = 1  # 0 < 2022; 1 >= 2022


class RD200(threading.Thread):
    def __init__(self, on_update):
        threading.Thread.__init__(self)
        self.on_update = on_update
        self.should_stop = threading.Event() # create an unset event on init
        self.Bq = None
        self.error = None
        self.t_next_read = time.time()
        self.t_next_send = time.time()

    def get_radon_value(self):
        Bq = None
        result = None
        try:
            command = "python radonreader/radon_reader.py -a {} -t {} -b -s".format(MAC_ADDRESS, TYPE).split()
            result = subprocess.run(command, stdout=subprocess.PIPE)
            Bq = float(result.stdout)
        except Exception as e:
            if result is not None:
                print(result)
            print(e)
        return Bq

    def run(self):
        while not self.should_stop.is_set():
            if time.time() >= self.t_next_read:
                self.t_next_read += 60  # next desired read in 60 seconds
                Bq = self.get_radon_value()
                if Bq is None:
                    error = True
                else:
                    error = False
                if (self.Bq != Bq) or (self.error != error) or (time.time() >= self.t_next_send):
                    self.t_next_send = time.time() + 570 # send next time in 9:30 (will sync to 10 minutes due to self.t_next_read)
                    self.Bq = Bq
                    self.error = error
                    self.on_update(self.Bq, self.error)

            t_sleep = self.t_next_read - time.time()
            if t_sleep > 1:
                t_sleep = 1  # do not wait longer than one second in order to stop asap
            if t_sleep < 0:
               t_sleep = 0  # avoid exception due to negative time
            time.sleep(t_sleep)

    def stop(self):
        self.should_stop.set()


cnt = 0
def main():
    # updates = 1 # will react immediatelly
    # updates = 2 # will need up to 10 minutes
    updates = 3 # will need up to 10 minutes plus (updates - 2) * 10 minutes
    def on_update(Bq, error):
        global cnt
        cnt += 1
        print(time.time(), "{}: {} Bq {}".format(cnt, Bq, "error" if error else ""))

    radon_reader = RD200(on_update)
    print(time.time(), "start")
    radon_reader.start()
    while cnt < updates:
        time.sleep(0.1)
    print(time.time(), "stop")
    radon_reader.stop()  # tell it to stop
    if radon_reader.is_alive():
        print(time.time(), "is_alive -> join")
        radon_reader.join()  # wait for termination
    print(time.time(), "done")


if __name__ == '__main__':
    main()
