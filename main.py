"""Стреляем!"""
from __future__ import annotations

from abc import ABC, abstractmethod

import cv2 as cv
import numpy as np

import config


class Robot:
    """
    Контекст определяет интерфейс, представляющий интерес для клиентов. Он также
    хранит ссылку на экземпляр подкласса Состояния, который отображает текущее
    состояние Контекста.
    """

    _state = None  # контекст

    def __init__(self, state: State) -> None:
        self.transition_to(state)

    def transition_to(self, state: State):
        """
        Контекст позволяет изменять объект Состояния во время выполнения.
        """
        self._state = state
        self._state.context = self
        if config.DEBUG:
            print(f"Context: Transition to {type(state).__name__}")

    def setup(self):
        """Все включаем, проверяем оборудование"""
        self._state.setup()

    def move(self):
        """Двигаем башенкой"""
        self._state.move()

    def laser_on(self):
        """Включаем лазер"""
        self._state.laser_on()

    def laser_off(self):
        """Выключаем лазер"""
        self._state.laser_off()

    def led_on(self):
        """Включаем лампочку"""
        self._state.led_on()

    def led_off(self):
        """Выключаем лампочку"""
        self._state.led_off()

    def buzz(self):
        """Навалить бассов"""
        self._state.buzz()

    def debug(self):
        """Отладочка"""
        self._state.debug()

    def button(self):
        """Получаем состояние кнопки"""
        self._state.button()


class State(ABC):
    """
    Базовый класс Состояния объявляет методы, которые должны реализовать все
    Конкретные Состояния, а также предоставляет обратную ссылку на объект
    Контекст, связанный с Состоянием. Эта обратная ссылка может использоваться
    Состояниями для передачи Контекста другому Состоянию.
    """

    @property
    def context(self) -> Robot:
        return self._context

    @context.setter
    def context(self, context: Robot) -> None:
        self._context = context

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def move(self):
        pass

    @abstractmethod
    def laser_on(self):
        pass

    @abstractmethod
    def laser_off(self):
        pass

    @abstractmethod
    def led_on(self):
        pass

    @abstractmethod
    def led_off(self):
        pass

    @abstractmethod
    def buzz(self):
        pass

    @abstractmethod
    def debug(self):
        pass

    @abstractmethod
    def button(self):
        pass


"""
Конкретные Состояния реализуют различные модели поведения, связанные с
состоянием Контекста.
"""


class Calibrate(State):
    """Все настраиваем перед заездом, ждем кнопочку"""


class BuildRoad(State):
    """Составляем маршрут"""


class Shoot(State):
    """Поражаем цель"""


def main():
    ...


if __name__ == "__main__":
    main()
