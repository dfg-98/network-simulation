from constants import SIGNAL_TIME
from .wire import Duplex
from .exceptions import PortNotConnectedError


class Port:
    """A Port represents a connection endpoint for a Device."""

    def __init__(self, port_name: str, write_callback=None) -> None:
        self.cable = None
        self.port_name = port_name
        self.write_callback = write_callback

    @property
    def name(self):
        return self.port_name

    def connect(self, cable: Duplex) -> None:
        """Try to connecto to the given wire. If wire is alredy connected,
        an WireConnectionError is raised."""
        self.cable = cable

    def disconnect(self):
        self.cable.disconnect(self)
        self.cable = None

    def write(self, value) -> None:
        """Write the value to the wire"""
        if self.cable is None:
            raise PortNotConnectedError(self)
        self.cable.write(self, value)

    def read(self, received=True) -> int:
        """Read the value from the wire"""
        if self.cable is None:
            raise PortNotConnectedError(self)
        return self.cable.read(self, received)

    def can_write(self) -> bool:
        """Indicates if port can write"""
        if self.cable is None:
            raise PortNotConnectedError(self)
        return self.cable.can_write(self)

    def __str__(self) -> str:
        return self.port_name
