from .bit import Bit
from .constants import SIGNAL_TIME
from .exceptions import PortNotConnectedError


class Wire:
    """Represents a physical wire"""

    def __init__(self, port1, port2, value: Bit = None) -> None:
        self.value = value


class Duplex:
    """Represents a duplex wire"""

    def __init__(self, port1, port2) -> None:
        self.wire1 = Wire(port1, port2)
        self.wire2 = Wire(port2, port1)
        self.time_to_reset = 0
        self.port1 = port1
        self.port2 = port2

    def write(self, port, value: Bit, time_to_reset: int = SIGNAL_TIME):
        if port == self.port1:
            self.wire1.value = value
            self.port2.write_callback()
        elif port == self.port2:
            self.wire2.value = value
            self.port1.write_callback()
        else:
            raise PortNotConnectedError(port)

    def read(self, port):
        if port == self.port1:
            return self.wire1.value
        elif port == self.port2:
            return self.wire2.value
        raise PortNotConnectedError(port)
