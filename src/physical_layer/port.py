from .constants import SIGNAL_TIME
from .wire import Duplex
from .exceptions import PortNotConnectedError


class Port:
    """A Port represents a connection endpoint for a Device."""

    def __init__(self, port_name: str, write_callback=None) -> None:
        self.cable = None
        self.port_name = port_name
        self.write_callback = write_callback

    def connect(self, cable: Duplex) -> None:
        """Try to connecto to the given wire. If wire is alredy connected,
        an WireConnectionError is raised."""
        self.cable = cable

    def write(self, value, time_to_reset: int = SIGNAL_TIME) -> None:
        """Write the value to the wire"""
        if self.cable is None:
            raise PortNotConnectedError(self)
        self.cable.write(value, self, time_to_reset)

    def read(self) -> int:
        """Read the value from the wire"""
        if self.cable is None:
            raise PortNotConnectedError(self)
        return self.cable.read(self)
