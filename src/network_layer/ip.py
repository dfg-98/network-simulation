from __future__ import annotations
from io import UnsupportedOperation
from typing import List, Tuple
from utils import (
    data_size,
    extend_to_byte_divisor,
    from_bit_data_to_hex,
    from_bit_data_to_number,
    from_number_to_bit_data,
)


PAYLOAD_TABLE = {
    0: "echo reply",
    3: "destination host unreachable",
    8: "echo request",
    11: "time exceeded",
}


class IP:
    """IP basic class

    Raises
    ------
    ValueError
        If the given values are not between 0 and 255
    """

    def __init__(self, *numbers):
        self.raw_value = 0
        for i in range(len(numbers)):
            num = numbers[-(i + 1)]
            if not 0 <= num <= 255:
                raise ValueError("IP numbers mut be between 0 and 255")

            self.raw_value += num << i * 8
        self.values = numbers

    @staticmethod
    def from_str(ip_str: str):
        values = [int(e) for e in ip_str.split(".")]
        return IP(*values)

    @staticmethod
    def from_bin(ip_bin: str):
        vals = []
        for i in range(len(ip_bin) // 8):
            vals.append(int(ip_bin[i * 8 : 8 + i * 8], base=2))
        return IP(*vals)

    def check_subnet(self, subnet, mask) -> bool:
        """Check if the IP belongs to a certain subnet using a given mask.

        Parameters
        ----------
        subnet : IP
            Subnet ip
        mask : IP
            Mask ip

        Returns
        -------
        bool
            True if the IP belongs to the subnet.
        """

        return self.raw_value & mask.raw_value == subnet.raw_value

    @property
    def str_binary(self):
        """str: Binary representation of the IP"""
        return f"{self.raw_value:032b}"

    @property
    def bit_data(self):
        """str: Binary representation of the IP"""
        return [int(b) for b in self.str_binary]

    def __repr__(self):
        """str: Value representation of the IP"""
        return ".".join([str(v) for v in self.values])

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, o: object) -> bool:
        return self.raw_value == o.raw_value

    @staticmethod
    def build_packet(dest_ip: IP, orig_ip: IP, data: List[int]) -> List[int]:
        packet = (
            dest_ip.bit_data
            + orig_ip.bit_data
            + [0] * 8
            + [0] * 8
            + data_size(data)
            + extend_to_byte_divisor(data)
        )

        return packet


class IPPacket:
    """Representa un paquete IP

    Parameters
    ----------
    dest_ip : IP
        Ip destino.
    orig_ip : IP
        Ip origen.
    payload : List[int]
        Datos a enviar.
    ttl : int, optional
        Time to live, by default 0
    protocol : int, optional
        Protocolo, by default 0

    Attributes
    ----------
    dest_ip : IP
        Ip destino.
    orig_ip : IP
        Ip origen.
    payload : List[int]
        Datos a enviar.
    ttl : int
        Time to live
    protocol : int
        Protocolo
    protocol_nmae : str
        Nombre del protocolo.
    bit_data : List[int]
        Paquete en forma de bits.
    """

    def __init__(
        self,
        dest_ip: IP,
        orig_ip: IP,
        payload: List[int],
        ttl: int = 0,
        protocol: int = 0,
    ) -> None:

        self.to_ip = dest_ip
        self.from_ip = orig_ip
        self.payload = payload

        self.ttl = from_number_to_bit_data(ttl)
        self.protocol = from_number_to_bit_data(protocol)
        self.protocol_number = protocol

    def __str__(self) -> str:
        payload_hex = from_bit_data_to_hex(self.payload)
        data = f"{self.from_ip} -> {self.to_ip} ({payload_hex})"
        return data

    @property
    def bit_data(self):
        return (
            self.to_ip.bit_data
            + self.from_ip.bit_data
            + self.ttl
            + self.protocol
            + data_size(self.payload)
            + extend_to_byte_divisor(self.payload)
        )

    @property
    def icmp_payload_msg(self) -> str:
        if self.protocol_number != 1:
            raise UnsupportedOperation("IP packet's protocol is not ICMP")
        payload_number = from_bit_data_to_number(self.payload)
        return PAYLOAD_TABLE.get(payload_number, "Unknown payload number")

    @staticmethod
    def ping(dest_ip: IP, orig_ip: IP) -> IPPacket:
        payload = from_number_to_bit_data(8)
        return IPPacket(dest_ip, orig_ip, payload, ttl=0, protocol=1)

    @staticmethod
    def pong(dest_ip: IP, orig_ip: IP) -> IPPacket:
        payload = from_number_to_bit_data(0)
        return IPPacket(dest_ip, orig_ip, payload, ttl=0, protocol=1)

    @staticmethod
    def no_dest_host(dest_ip: IP, orig_ip: IP) -> IPPacket:
        payload = from_number_to_bit_data(3)
        return IPPacket(dest_ip, orig_ip, payload, ttl=0, protocol=1)

    @staticmethod
    def parse(data: List[int]) -> Tuple[bool, IPPacket]:
        """Convierte una serie de bits a un paquete ip si es posible.

        Parameters
        ----------
        data : List[int]
            Datos en forma de bits.

        Returns
        -------
        bool
            True si los datos enforma de bits son válidos.
        IPPacket
            Packete creado.
        """

        if len(data) < 88:
            return False, None

        ip_dest = IP.from_bin("".join(map(str, data[:32])))
        ip_orig = IP.from_bin("".join(map(str, data[32:64])))
        ttl = from_bit_data_to_number(data[64:72])
        protocol = from_bit_data_to_number(data[72:80])
        payload_s = from_bit_data_to_number(data[80:88])

        total_size = 88 + payload_s * 8

        if len(data) < total_size:
            return False, None

        bit_data = data[88 : 88 + payload_s * 8]
        packet = IPPacket(ip_dest, ip_orig, bit_data, ttl, protocol)
        return True, packet
