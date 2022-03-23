from .device import Device
from .wire import Wire
from .exceptions import WireConnectionError, PortNotConnectedError


class Port:
    """A Port represents a connection endpoint for a Device.

    A port has a reference to his device
    """

    device: Device
    wire: Wire

    def __init__(self, device: Device) -> None:
        self.device = device

    def connect(self, wire: Wire) -> None:
        """Try to connecto to the given wire. If wire is alredy connected,
        an WireConnectionError is raised."""
        if wire.port1 is None:
            wire.port1 = self
        elif wire.port2 is None:
            wire.port2 = self
        else:
            raise WireConnectionError(wire)
        self.wire = wire

    def write(self, value) -> None:
        """Write the value to the wire"""
        if self.wire is None:
            raise PortNotConnectedError(self)
        self.wire.value = value

    def read(self) -> int:
        """Read the value from the wire"""
        if self.wire is None:
            raise PortNotConnectedError(self)
        return self.wire.value

    def wire_written(self):
        pass