from __future__ import annotations
from typing import List, Dict
from datalink_layer.frame_sender import FrameSender
from utils import (
    from_str_to_bit_data,
)
from .ip import IP, IPPacket


class IPPacketSender(FrameSender):
    """
    Representa un dispositivo capaz de enviar pacquetes IP.

    Attributes
    ----------
    ips: Dict[int, IP]
        Tabla que contiene la dirección IP de cada puerto.
    masks: Dict[int, IP]
        Tabla que contiene la máscara del IP de cada puerto.
    ip_table: Dict[int, List[int]]
        Tabla que contiene la dirección MAC de los dispositivos según
        la dirección IP.
    waiting_for_arpq: Dict[int, List[List[int]]]
        Tabla que contiene paquetes que esán en espera de una respuesta del
        protocolo ARPQ para ser enviados.
    """

    def __init__(self, name: str, ports_count: int):
        self.ips: Dict[str, IP] = {}
        self.masks: Dict[int, IP] = {}
        self.ip_table: Dict[str, List[int]] = {}
        self.waiting_for_arpq: Dict[str, List[List[int]]] = {}
        super().__init__(name, ports_count)

    def make_arpq(self, ip: IP, port: str):
        """
        Envía un broadcast siguiendo el protocolo ARP para obtener la
        mac de un IP determinado.

        Parameters
        ----------
        ip : IP
            Ip del cual se quiere obtener la mac.
        """

        arpq = from_str_to_bit_data("ARPQ")
        ip_data = ip.bit_data
        self.send_frame([1] * 16, arpq + ip_data, port)

    def respond_arpq(self, dest_mac: List[int], port: str) -> None:
        """
        Envía un frame que responde a un llamado ARPQ.

        Parameters
        ----------
        dest_mac : List[int]
            Mac destino.
        port : int, optional
            Puerto por el cual se envía, por defecto 1
        """

        arpq = from_str_to_bit_data("ARPQ")
        ip_data = self.ips[port].bit_data
        self.send_frame(dest_mac, arpq + ip_data, port)

    def send_ip_packet(
        self, packet: IPPacket, port: str, ip_dest: IP = None
    ) -> None:
        """
        Envía un IP packet.

        Parameters
        ----------
        packet : IPPacket
            Paquete a enviar.
        port : int, optional
            Puerto por el cual se envía, por defecto 1
        ip_dest : IP, optional
            IP destno, por defecto None
        """

        if ip_dest is None:
            ip_dest = packet.to_ip
        ip_dest_str = str(ip_dest)
        if ip_dest_str not in self.ip_table:
            if ip_dest_str not in self.waiting_for_arpq:
                self.waiting_for_arpq[ip_dest_str] = []
            self.waiting_for_arpq[ip_dest_str].append(packet.bit_data)
            self.make_arpq(ip_dest, port)
        else:
            self.send_frame(self.ip_table[ip_dest_str], packet.bit_data, port)

    def send_by_ip(self, ip_dest: IP, data: List[int], port: str) -> None:
        """
        Envía los datos dados a un IP determinado.

        Parameters
        ----------
        ip_dest : IP
            Ip destino.
        data : List[int]
            Datos a enviar.
        port : int, optional
            Puerto por el cual se envía, por defecto 1
        """

        self.send_ip_packet(IPPacket(ip_dest, self.ips[port], data), port)
