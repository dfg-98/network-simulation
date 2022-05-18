import time
from typing import List

from physical_layer.bit import Bit
from physical_layer.device import Device
from physical_layer.host import Host
from physical_layer.wire import Wire
from physical_layer.port import Port
from config import check_config, CONFIG
from physical_layer.constants import SIGNAL_TIME


class Simulation:
    def __init__(self, output_path: str = "output"):
        check_config()
        self.instructions = []
        self.devices = {}
        self.hosts = {}
        self.ports = {}
        self.wires = []
        global SIGNAL_TIME
        SIGNAL_TIME = CONFIG["signal_time"]
        self.output_path = output_path
        self.end_delay = SIGNAL_TIME
        self.inst_index = 0
        self.time = 0

    def add_device(self, device: Device):
        print(f"Adding device {device.name}")
        if device.name in self.devices.keys():
            raise ValueError(
                f"The device name {device.name} is already taken."
            )

        self.devices[device.name] = device
        for port in device.ports.values():
            self.ports[port.port_name] = port

        if isinstance(device, Host):
            self.hosts[device.name] = device

    def connect(self, port_1: str, port_2: str):
        try:
            port1 = self._get_port_by_name(port_1)
            port2 = self._get_port_by_name(port_2)
        except KeyError as e:
            if port_1 not in self.ports.keys():
                raise ValueError(f"Port {port_1} does not exist.")
            if port_2 not in self.ports.keys():
                raise ValueError(f"Port {port_2} does not exist.")

        wire = Wire(port1=port1, port2=port2)

        self.wires.append(wire)

    def send(self, host_name: str, data: List[Bit]):
        if host_name not in self.devices.keys():
            raise ValueError(f"Host {host_name} does not exist.")

        host = self._get_host_by_name(host_name)
        host.send(data)

    def disconnect(self, port_name: str):
        if port_name not in self.ports.keys():
            raise ValueError(f"Port {port_name} does not exist.")
        self._get_port_by_name(port_name).disconnect()

    def start(self, instructions):
        """
        Comienza la simulación dada una lista de instrucciones.

        Parameters
        ----------
        instructions : List[Instruction]
            Lista de instrucciones a ejecutar en la simulación.
        """

        self.instructions = instructions
        self.time = 0
        while self.is_running:
            self.update()
        for device in self.devices.values():
            device.save_log(self.output_path)

    @property
    def is_running(self):
        """
        bool : Indica si la simulación todavía está en ejecución.
        """

        device_sending = any(
            [(d.is_sending or d.time_to_send) for d in self.hosts.values()]
        )
        running = self.instructions or device_sending
        if not running:
            self.end_delay -= 1
        return self.end_delay > 0

    def update(self):
        """
        Ejecuta un ciclo de la simulación actualizando el estado de la
        misma.

        Esta función se ejecuta una vez por cada milisegundo simulado.
        """
        # print(self.time, self.devices)
        current_insts = []
        while self.instructions and self.time == self.instructions[0].time:
            current_insts.append(self.instructions.pop(0))

        for instr in current_insts:
            instr.execute(self)

        for device in self.devices.values():
            device.reset()

        for host in self.hosts.values():
            host.update(self.time)

        for device in self.devices.values():
            if device not in self.hosts.values():
                device.update(self.time)
        for host in self.hosts.values():
            host.receive()

        for wire in self.wires:
            wire.update()

        self.time += 1

    def _get_port_by_name(self, port_name) -> Port:
        return self.ports[port_name]

    def _get_host_by_name(self, host_name) -> Host:
        return self.devices[host_name]
