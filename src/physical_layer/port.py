from .constants import SIGNAL_TIME
from .wire import Wire
from .exceptions import PortNotConnectedError


class Port:
    """A Port represents a connection endpoint for a Device."""

    def __init__(self, port_name: str, written_callback=None) -> None:
        self.wire = None
        self.port_name = port_name
        self.written_callback = written_callback

    def connect(self, wire: Wire) -> None:
        """Try to connecto to the given wire. If wire is alredy connected,
        an WireConnectionError is raised."""
        self.wire = wire

    def write(self, value, time_to_reset: int = SIGNAL_TIME) -> None:
        """Write the value to the wire"""
        if self.wire is None:
            raise PortNotConnectedError(self)
        self.wire.write(value, time_to_reset)

    def read(self) -> int:
        """Read the value from the wire"""
        if self.wire is None:
            raise PortNotConnectedError(self)
        return self.wire.value
