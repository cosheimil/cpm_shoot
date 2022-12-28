"""Стреляем!"""
import cv2 as cv
import numpy as np

import const


class Sniper(object):
    """Главный класс для робота

    Args:
        object (Nan): __init__

    Returns:
        NaN: NaN
    """

    name = "state"
    allowed = ["take_aim", "shoot", "wait"]

    def switch(self, state):
        """Switch to new state"""
        if state.name in self.allowed and const.DEBUG:
            print("Current:", self, " => switched to new state", state.name)
            self.__class__ = state
        else:
            print("Current:", self, " => switching to", state.name, "not possible.")

    def __str__(self):
        return self.name


class Off(Sniper):
    name = "off"
    allowed = ["on"]


class On(Sniper):
    """State of being powered on and working"""

    name = "on"
    allowed = ["off", "suspend", "hibernate"]


class Suspend(Sniper):
    """State of being in suspended mode after switched on"""

    name = "suspend"
    allowed = ["on"]


class Hibernate(Sniper):
    """State of being in hibernation after powered on"""

    name = "hibernate"
    allowed = ["on"]


def main():
    ...


if __name__ == "__main__":
    main()
