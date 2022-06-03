from math import ceil
from typing import List


def from_number_to_bit_data(number: int, size: int = 8):
    data = [int(b) for b in f"{number:b}"]
    if len(data) > size:
        return data[-size:]
    elif len(data) < size:
        data = [0] * (size - len(data)) + data
    return data


def from_bit_data_to_number(data: List[int]):
    """Convierte los datos de una lista de bits a un número en base decimal.

    Parameters
    ----------
    data : List[int]
        Datos a convertir.

    Returns
    -------
    int
        Número resultante.
    """

    return int("".join([str(bit) for bit in data]), 2)


def from_str_to_bin(s: str):
    return "".join([f"{ord(c):08b}" for c in s])


def from_str_to_bit_data(s: str):
    return [int(b) for b in from_str_to_bin(s)]


def from_bit_data_to_hex(data: List[int]):
    number = from_bit_data_to_number(data)
    hex_data = str(hex(number))[2:].upper()
    if len(hex_data) % 4 != 0:
        rest = 4 - len(hex_data) % 4
        hex_data = "0" * rest + hex_data
    return hex_data


def data_size(data):
    size_str = f"{ceil(len(data)/8):b}"
    size = [0] * 8

    for i in range(1, len(size_str) + 1):
        size[-i] = int(size_str[-i])
    return size


def extend_to_byte_divisor(data, at_end=True):
    if len(data) % 8 != 0:
        rest = 8 - len(data) % 8
        if at_end:
            return data + [0] * rest
        else:
            return [0] * rest + data
    return data
