from typing import List, Tuple

from .bit import VoltageDecodification as VD
from .utils import from_bit_data_to_number


def _simple_hash(frame: List[VD]) -> Tuple[List[VD], bool]:
    correction_size = from_bit_data_to_number(frame[40:48])
    data = frame[48 : len(frame) - 8 * correction_size]
    correction_data = frame[-8 * correction_size :]
    return frame, sum(i.value for i in data) != from_bit_data_to_number(
        correction_data
    )


def check_frame_correction(
    frame: List[int], error_det_algorithm: str
) -> Tuple[List[int], bool]:
    if error_det_algorithm == "simple_hash":
        return _simple_hash(frame)
    else:
        raise ValueError("Invalid error detection algorithm")


def _get_simple_hash(data: List[List[VD]]) -> Tuple[List[VD], List[VD]]:
    data_sum = sum([i.value for i in data])
    bit_data_sum = f"{data_sum:b}"
    if len(bit_data_sum) % 8 != 0:
        rest = 8 - len(bit_data_sum) % 8
        bit_data_sum = "0" * rest + bit_data_sum
    error_correction = [VD(int(b)) for b in bit_data_sum]
    error_correction_size = [
        VD(int(b)) for b in f"{len(bit_data_sum) // 8:08b}"
    ]
    return error_correction_size, error_correction


def get_error_detection_data(
    data: List[VD], error_det_algorithm: str
) -> Tuple[List[VD], List[VD]]:
    if error_det_algorithm == "simple_hash":
        return _get_simple_hash(data)
    else:
        raise ValueError("Invalid error detection algorithm")
