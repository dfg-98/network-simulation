from .port import Port


class Wire:
    """A wire connects two devices

    Collisions can occurs if two devices writes at the same time

    """

    _value = None
    port1 = None
    port2 = None

    def __init__(self, port1=None, port2=None) -> None:
        self.port1 = port1
        self.port2 = port2

    @property
    def value(self):
        return self._value

    def clear(self):
        """Clear the value of the wire"""
        self.value = None

    def connect(self, port1: Port, port2: Port):
        """Connect the two ports.
        Use Port.connect method to connect the ports.
        """
        self.port1 = self.port2 = None
        port1.connect(self)
        port2.connect(self)

    def write(self, value):
        """Write the value to the wire"""
        self._value = value
        self.port1.wire_written()
        self.port2.wire_written()