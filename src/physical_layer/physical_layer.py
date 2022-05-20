from typing import List
from random import randint

from .bit import VoltageDecodification as VD
from .constants import SIGNAL_TIME
from .port import Port


class PhysicalLayer:
    """Class that knows how to send and read information
    at physical layer level
    """

    def __init__(self, port: Port) -> None:
        self.port = port
        # Register write callback for detect collisions
        self.port.write_callback = self.port_was_written

        self.data = []
        self.current_package = []
        self.package_index = 0
        self.time_to_send = 0
        self.read_time = 0
        self.max_time_to_send = SIGNAL_TIME
        self.send_time = 0
        self.is_sending = False
        self.time_connected = 0
        self.received_bit = VD.NULL
        (
            self.on_send_callbacks,
            self.on_receive_callbacks,
            self.on_collision_callbacks,
        ) = ([], [], [])

    @property
    def is_active(self):
        return (
            self.is_sending or self.time_to_send > 0
        ) and self.port.cable is not None

    def extend_max_time_to_send(self):
        self.max_time_to_send *= 2

    def load_package(self):
        if not self.current_package:
            if self.data:
                self.current_package = self.data.pop(0)
                self.max_time_to_send = SIGNAL_TIME
                self.package_index = 0
                self.send_time = 0
                self.is_sending = True
            elif self.is_sending:
                self.sending_bit = VD.NULL
                self.is_sending = False
                self.port.write(VD.NULL)

    def send(self, data: List[List[VD]]):
        """Add new data to be sent"""
        self.data += data

    def update(self):
        """
        Update the state of the component.

        """

        if self.port is None or self.port.cable is None:
            return

        self.time_connected += 1

        if self.read_time > 0:
            self.read_time -= 1

        if self.read_time == 0:
            if self.received_bit == VD.COLLISION:

                if self.is_sending:
                    self.wait_for_network_availability()
                    for callback in self.on_collision_callbacks:
                        callback()
            elif self.received_bit != VD.NULL:
                for callback in self.on_receive_callbacks:
                    callback(self.received_bit)
            self.read_time = SIGNAL_TIME

        self.load_package()

        if self.time_to_send:
            self.time_to_send -= 1

        if self.time_to_send:
            return

        if self.current_package:
            self.is_sending = True
            self.sending_bit = self.current_package[self.package_index]

            if self.send_time == 0:
                can_write = self.port.can_write()
                if can_write:
                    self.port.write(self.sending_bit)
                    for callback in self.on_send_callbacks:
                        callback(self.sending_bit)
                else:
                    self.wait_for_network_availability()
                    return
            self.send_time += 1
            if self.send_time == SIGNAL_TIME:
                self.package_index += 1
                if self.package_index == len(self.current_package):
                    self.current_package = []
                self.send_time = 0

    def wait_for_network_availability(self):
        """
        Wait for the network to be available
        """

        self.time_to_send = randint(1, self.max_time_to_send) * SIGNAL_TIME
        self.extend_max_time_to_send()
        self.package_index = 0
        self.send_time = 0
        self.is_sending = False

    def port_was_written(self):
        if self.read_time == 0:
            self.read_time = SIGNAL_TIME

        self.received_bit = self.port.read()

    def disconnect(self):
        """
        Disconnects the physical layer from the port
        """

        self.port.disconnect()

        # Reset sending info
        if self.current_package:
            self.data.insert(0, self.current_package)
        self.current_package = []
        self.package_index = 0
        self.is_sending = False
        self.send_time = 0
        self.sending_bit = None
        self.max_time_to_send = SIGNAL_TIME
        self.time_connected = 0
        self.received_bits = []
