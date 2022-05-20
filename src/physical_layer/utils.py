from typing import List

from .bit import VoltageDecodification as VD


def from_bit_data_to_number(data: List[VD]):
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
