from collections import Counter
from functools import reduce
from typing import List
from random import randint

from .constants import SIGNAL_TIME
from .device import Device
from .port import Port
from .wire import Wire
from .bit import Bit


class Host(Device):
    """Represents a Host"""

    def __init__(self, name: str) -> None:
        ports = {f"{name}_1": Port(f"{name}_1")}
        super().__init__(name, ports)
        self.data = []
        self.current_package = []
        self.package_index = 0
        self.time_to_send = 0
        self.max_time_to_send = 2
        self.send_time = 0
        self.sending_bit = None
        self.is_sending = False
        self.time_connected = 0
        self.simulation_time = 0
        self.recived_bits = []

    @property
    def port(self) -> Port:
        """Returns host's port"""
        return self.ports[self.port_name(1)]

    def readjust_max_time_to_send(self):
        self.max_time_to_send *= 2

    def load_package(self):
        """
        Load next package to send if there are data
        """
        if not self.current_package:
            if self.data:
                self.current_package = self.data[:8]
                self.data = self.data[8:]
                self.max_time_to_send = 1
                self.package_index = 0
                self.send_time = 0
                self.is_sending = True
            elif self.is_sending:
                self.sending_bit = None
                self.is_sending = False

    def send(self, data: List[Bit]):
        """
        Add data to be sent

        Parameters
        ----------
        data : List[int]
        """
        self.data += data

    def receive(self):
        """
        Read from port's connected wire

        If host is sending information checks for collisions.
        Otherwise it store the reading between two SIGNAL_TIME
        """
        if self.is_sending:
            self.check_collision()

        if self.is_sending:
            return

        if self.time_connected % SIGNAL_TIME // 2 == 0:
            if self.port.wire is not None:
                val = self.port.read()
                if val is not None:
                    self.recived_bits.append(val)

        if self.time_connected % SIGNAL_TIME == 0 and self.recived_bits:
            temp = [(v, k) for k, v in Counter(self.recived_bits).items()]
            self.log(
                self.simulation_time,
                "Received",
                f"{max(temp, key=lambda x: x[0]  )[1]}",
            )
            self.recived_bits = []

    def check_collision(self):
        """
        Check if collision happens
        Returns
        -------
        bool
            ``True`` if collision, ``False`` otherwise.
        """
        if self.is_sending and self.port.read() != self.sending_bit:
            self.time_to_send = randint(1, self.max_time_to_send) * SIGNAL_TIME
            self.readjust_max_time_to_send()
            self.log(
                self.simulation_time,
                "Collision",
                f"Waitting {self.time_to_send}ms to send",
            )
            self.package_index = 0
            self.send_time = 0
            self.is_sending = False
            return True
        return False

    def connect(self, wire: Wire, port_name: str):
        if self.port.wire is not None:
            raise ValueError(f"Port {port_name} is currently in use.")

        self.ports[self.port_name(1)].connect(wire)
        self.logs(self.simulation_time, "Connected")

    def disconnect(self, port_name: str):
        self.data = self.current_package + self.data
        self.current_package = []
        self.package_index = 0
        self.is_sending = False
        self.send_time = 0
        self.sending_bit = 0
        self.max_time_to_send = 2
        self.time_connected = 0
        self.recived_bits = []
        super().disconnect(port_name)
        self.log(self.simulation_time, "Disconnected")

    def update(self, time):
        super().update(time)

        if self.time_to_send:
            self.time_to_send -= 1

        if self.time_to_send:
            self.time_connected += 1
            return

        if self.is_sending and self.check_collision():
            self.time_connected += 1
            return

        self.load_package()

        if self.current_package:

            self.is_sending = True
            self.sending_bit = self.current_package[self.package_index]
            # self.log(time, f"Trying to send {self.sending_bit}")

            self.port.write(self.sending_bit)
            if self.send_time == 0:
                self.log(self.simulation_time, "Sent", f"{self.sending_bit}")
            self.send_time += 1
            if self.send_time == SIGNAL_TIME:
                self.package_index += 1
                if self.package_index == len(self.current_package):
                    self.current_package = []
                self.send_time = 0

        self.time_connected += 1
