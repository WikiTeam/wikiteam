import itertools
import threading
import time
import sys

from wikiteam3.dumpgenerator.config import Config, DefaultConfig

class Delay:

    done: bool = True
    ellipses: str = "."

    def animate(self):
        try:
            while not self.done:
                sys.stdout.write("\r    " + self.ellipses)
                sys.stdout.flush()
                self.ellipses += "."
                time.sleep(0.1)
        except KeyboardInterrupt:
            sys.exit()

    def __init__(self, config: Config=None, session=None):
        """Add a delay if configured for that"""
        if config.delay > 0:
            self.done = False

            ellipses_animation = threading.Thread(target=self.animate)
            ellipses_animation.start()

            # sys.stdout.write("\rSleeping %.2f seconds..." % (config.delay))
            # sys.stdout.flush()

            time.sleep(config.delay)
            self.done = True

            sys.stdout.write("\r                           \r")
            sys.stdout.flush()
