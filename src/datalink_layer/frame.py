from __future__ import annotations
from typing import List
from random import randint, random
from config import CONFIG
from datalink_layer.error_detection import get_error_detection_data
from network_layer.ip import IPPacket, IP
from physical_layer.bit import VoltageDecodification as VD
from utils import (
    data_size,
    extend_to_byte_divisor,
    from_bit_data_to_hex,
    from_bit_data_to_number,
    from_number_to_bit_data,
    from_str_to_bin,
)


class Frame:
    def __init__(self, bit_data: List[int]) -> None:
        self.is_valid = False

        if len(bit_data) < 48:
            return

        self.to_mac = from_bit_data_to_number(bit_data[:16])
        self.from_mac = from_bit_data_to_number(bit_data[16:32])
        self.frame_data_size = from_bit_data_to_number(bit_data[32:40]) * 8
        self.error_size = from_bit_data_to_number(bit_data[40:48]) * 8
        total_size = self.frame_data_size + self.error_size

        if len(bit_data) - 48 < total_size:
            return

        top_data_pos = 48 + 8 * self.frame_data_size
        self.data = bit_data[48:top_data_pos]
        self.error_data = bit_data[
            top_data_pos : top_data_pos + 8 * self.error_size
        ]
        self.bit_data = bit_data
        self.is_valid = True
        self.additional_info = ""

        if self.frame_data_size / 8 == 8:
            arpq = from_str_to_bin("ARPQ")
            ip = "".join(map(str, self.data[32:64]))
            mac_dest_str = "".join(map(str, bit_data[:16]))
            arpq_data = "".join(map(str, self.data[:32]))
            if arpq_data.endswith(arpq):
                if mac_dest_str == "1" * 16:
                    self.additional_info = f"(ARPQ) Who is {IP.from_bin(ip)} ?"
                else:
                    self.additional_info = "(ARPQ) response"

    def __str__(self) -> str:
        from_mac = from_bit_data_to_hex(
            from_number_to_bit_data(self.from_mac, 16)
        )
        to_mac = from_bit_data_to_hex(from_number_to_bit_data(self.to_mac, 16))

        data = from_bit_data_to_hex(self.data)
        valid, packet = IPPacket.parse(self.data)
        if valid:
            data = str(packet)

        return f"{from_mac} -> {to_mac} | {data} | {self.additional_info}"

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def build(
        dest_mac: List[int], orig_mac: List[int], data: List[int]
    ) -> Frame:
        data = extend_to_byte_divisor(data)

        e_size, e_data = get_error_detection_data(
            data, CONFIG["error_detection"]
        )

        rand = random()
        if rand < CONFIG["error_prob"]:
            ind = randint(0, len(data) - 1)
            data[ind] = VD((data[ind] + 1) % 2)

        size = data_size(data)
        final_data = dest_mac + orig_mac + size + e_size + data + e_data

        frame = Frame(final_data)
        return frame
