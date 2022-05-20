from .bit import VoltageDecodification
from .constants import SIGNAL_TIME
from .exceptions import PortNotConnectedError, TryToWriteOnTransmission


class Wire:
    """Represents a physical wire"""

    def __init__(self) -> None:
        self.value: VoltageDecodification = VoltageDecodification.NULL
        self.time_to_reset = 0

    def write(self, value: VoltageDecodification):
        if self.time_to_reset != 0:
            value = VoltageDecodification.COLLISION
        self.value = value
        self.time_to_reset = SIGNAL_TIME

    def update(self):
        if self.value == VoltageDecodification.COLLISION:
            self.time_to_reset = 0
        if self.time_to_reset == 0:
            self.value = VoltageDecodification.NULL
        elif self.time_to_reset > 0:
            self.time_to_reset -= 1

    def can_write(self) -> bool:
        return self.time_to_reset == 0 or self.time_to_reset == SIGNAL_TIME


class Duplex:
    """Represents a duplex wire"""

    def __init__(self, port1, port2) -> None:
        self.wire1 = Wire()
        self.wire2 = Wire()
        self.port1 = port1
        self.port2 = port2
        self.port1.connect(self)
        self.port2.connect(self)

    def can_write(self, port):
        """Indicates if port can write on its respective wire"""
        if port == self.port1:
            return self.wire1.can_write()
        if port == self.port2:
            return self.wire2.can_write()

        raise PortNotConnectedError(port)

    def write(self, port, value: VoltageDecodification):
        if port == self.port1:
            self.wire1.write(value)
            self.port2.write_callback()
        elif port == self.port2:
            self.wire2.write(value)
            self.port1.write_callback()
        else:
            raise PortNotConnectedError(port)

    def read(self, port, received=True) -> VoltageDecodification:
        if port == self.port1:
            return self.wire2.value if received else self.wire1.value
        elif port == self.port2:
            return self.wire1.value if received else self.wire2.value
        raise PortNotConnectedError(port)

    def update(self):
        self.wire1.update()
        self.wire2.update()

    def disconnect(self, port):
        if port == self.port1:
            self.port2.cable = None
        elif port == self.port2:
            self.port1.cable = None
        else:
            raise PortNotConnectedError(port)

        self.port1 = None
        self.port2 = None
