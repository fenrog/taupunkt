import time
from threading import Timer
from datetime import datetime

class TimeSyncedTimer(Timer):
    def run(self):
        t = time.time()
        d = self.interval - (t % self.interval)
        while not self.finished.wait(d):
            self.function(*self.args, **self.kwargs)
            t = time.time()
            d = self.interval - (t % self.interval)


def main():
    def dummyfn(msg="foo"):
        print(datetime.now().strftime("%d.%m.%y %H:%M:%S.%d"), msg)

    timer = TimeSyncedTimer(1, dummyfn)
    timer.start()
    time.sleep(5)
    timer.cancel()

    timer = TimeSyncedTimer(2, dummyfn, ["arg1"])
    timer.start()
    time.sleep(10)
    timer.cancel()

    timer = TimeSyncedTimer(5, dummyfn, args=("arg2",))
    timer.start()
    time.sleep(20)
    timer.cancel()

    timer = TimeSyncedTimer(10, dummyfn, [], {"msg":"kwarg1"})
    timer.start()
    time.sleep(50)
    timer.cancel()

    timer = TimeSyncedTimer(1, dummyfn, kwargs={"msg":"kwarg2"})
    timer.start()
    time.sleep(5)
    timer.cancel()


if __name__ == '__main__':
    main()
