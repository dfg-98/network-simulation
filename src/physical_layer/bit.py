import enum


class VoltageDecodification(enum.Enum):
    """
    Enum for the bit values.
    """

    NULL = -1
    ZERO = 0
    ONE = 1
    COLLISION = 2

    def __str__(self) -> str:
        if self.value == -1:
            return "Null"
        if self.value == 2:
            return "Coll"
        return str(self.value)
