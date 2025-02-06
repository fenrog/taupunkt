import sys
import time
import signal
from Model import Model
from View import View
from Controller import Controller


view = None
controller = None


def signal_handler(sig, frame):
    global view
    global controller
    print('Terminated with Ctrl+C!')
    if view:
        view.stop()
    if controller:
        controller.stop()
    sys.exit(0)


def setup():
    global view
    global controller
    signal.signal(signal.SIGINT, signal_handler)
    print('Terminate with Ctrl+C')
    view = View()
    model = Model(view)
    view.start()
    controller = Controller(model)
    controller.start()


def main():
    setup()
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
