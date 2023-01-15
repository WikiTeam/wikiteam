import itertools
import threading
import time
import sys

from wikiteam3.dumpgenerator.config import Config

class Delay:
    done: bool = False
    lock: threading.Lock = threading.Lock()
    ellipses: str = "."

    def animate(self):
        while True:
            with self.lock:
                if self.done:
                    return

                print("\r" + self.ellipses, end="")
                self.ellipses += "."

            time.sleep(0.1)

    def __init__(self, config: Config=None, session=None):
        """Add a delay if configured for that"""
        if config.delay > 0:
            ellipses_animation = threading.Thread(target=self.animate)
            ellipses_animation.daemon = True
            ellipses_animation.start()

            time.sleep(config.delay)

            with self.lock:
                self.done = True
                print("\r" + " " * len(self.ellipses) + "\r", end="")
