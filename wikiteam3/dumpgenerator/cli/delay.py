import itertools
import threading
import time
import sys

from wikiteam3.dumpgenerator.config import Config

class Delay:
    done: bool = False
    lock: threading.Lock = threading.Lock()

    def animate(self):
        while True:
            with self.lock:
                if self.done:
                    return

                print("\r" + self.ellipses, end="")
                self.ellipses += "."

            time.sleep(0.3)

    def __init__(self, config: Config=None, session=None, msg=None, delay=None):
        """Add a delay if configured for that"""
        self.ellipses: str = "."

        if delay is None:
            delay = config.delay
        if delay <= 0:
            return

        if msg:
            self.ellipses = ("Delay %.1fs: %s " % (delay, msg)) + self.ellipses
        else:
            self.ellipses = ("Delay %.1fs " % (delay)) + self.ellipses

        ellipses_animation = threading.Thread(target=self.animate)
        ellipses_animation.daemon = True
        ellipses_animation.start()

        time.sleep(delay)

        with self.lock:
            self.done = True
            print("\r" + " " * len(self.ellipses) + "\r", end="")
