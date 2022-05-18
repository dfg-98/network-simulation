from .bit import Bit
from .constants import SIGNAL_TIME


class Wire:
    """Represents a physical wire"""

    def __init__(self, port1, port2, value: Bit = None) -> None:
        self.value = value
        self.time_to_reset = 0
        self.port1 = port1
        self.port2 = port2
        self.port1.connect(self)
        self.port2.connect(self)

    def update(self):

        if self.value is not None and self.time_to_reset == 0:
            self.value = None
        elif self.time_to_reset > 0:
            self.time_to_reset -= 1

    def write(self, value: Bit, time_to_reset: int = SIGNAL_TIME):
        self.value = value
        self.time_to_reset = time_to_reset

        if self.port1.written_callback:
            self.port1.written_callback(self.port1)
        if self.port2.written_callback:
            self.port2.written_callback(self.port2)
        return self.value
