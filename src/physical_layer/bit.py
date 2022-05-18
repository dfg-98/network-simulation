import enum


class Bit(enum.Enum):
    """
    Enum for the bit values.
    """

    ZERO = 0
    ONE = 1

    def __str__(self) -> str:
        return str(self.value)
