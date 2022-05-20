from __future__ import annotations


class WireConnectionError(Exception):
    """
    Exception raised when a wire connection is not possible.
    """

    def __init__(self, wire: "Wire") -> None:
        super().__init__()
        self.wire = wire

    def __str__(self) -> str:
        assert self.wire.port1 is not None and self.wire.port2 is not None
        return (
            f"Cannot connect wire. {self.wire.port1}"
            " and {self.wire.port2} are busy."
        )


class PortNotConnectedError(Exception):
    """
    Exception raised when a port is not connected to a wire.
    """

    def __init__(self, port: "Port") -> None:
        super().__init__()
        self.port = port

    def __str__(self) -> str:
        return f"Port {self.port} is not connected to a wire."


class TryToWriteOnTransmission(Exception):
    """
    Exception raised when a port try to write but wire is on transmission
    """

    def __init__(self, port: "Port", wire: "Wire") -> None:
        super().__init__()
        self.port = port
        self.wire = wire

    def __str__(self) -> str:
        return f"Port {self.port} try to write on wire {self.wire} but wire is on transmission."
