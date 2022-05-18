import time
from threading import Lock

from physical_layer.device import Device
from physical_layer.host import Host
from physical_layer.wire import Wire
from physical_layer.port import Port
from config import check_config, CONFIG
from timer import GLOBAL_TIMER


class Simulation:

    devices = dict()
    ports = dict()
    wires = []
    lock = Lock()

    def __init__(self, output_path: str = "output"):
        check_config()
        self.instructions = []
        self.signal_time = CONFIG["signal_time"]
        self.output_path = output_path

    def add_device(self, device: Device):
        self.lock.acquire()
        print(f"Adding device {device.name}")
        if device.name in self.devices.keys():
            self.lock.release()
            raise ValueError(
                f"The device name {device.name} is already taken."
            )

        self.devices[device.name] = device
        for port in device.ports.values():
            print(f"Adding port {port.port_name}")
            self.ports[port.port_name] = port
        self.lock.release()

    def connect(self, port_1: str, port_2: str):
        self.lock.acquire()
        print(
            f"Connecting: {port_1} - {port_2}. Existing ports: {self.ports.keys()}"
        )
        try:
            port1 = self._get_port_by_name(port_1)
            port2 = self._get_port_by_name(port_2)
        except KeyError as e:
            time.sleep(1)
            if port_1 not in self.ports.keys():
                self.lock.release()
                raise ValueError(f"Port {port_1} does not exist.")
            if port_2 not in self.ports.keys():
                self.lock.release()
                raise ValueError(f"Port {port_2} does not exist.")
            port1 = self._get_port_by_name(port_1)
            port2 = self._get_port_by_name(port_2)

        wire = Wire()
        port1.connect(wire)
        port2.connect(wire)
        self.wires.append(wire)
        self.lock.release()

    def send(self, host_name: str, data: str):
        self.lock.acquire()
        if host_name not in self.devices.keys():
            self.lock.release()
            raise ValueError(f"Host {host_name} does not exist.")

        host = self._get_host_by_name(host_name)
        for bit in data:
            host.send(bit)
        self.lock.release()

    def disconnect(self, port_name: str):
        self.lock.acquire()
        if port_name not in self.ports.keys():
            self.lock.release()
            raise ValueError(f"Port {port_name} does not exist.")
        self._get_port_by_name(port_name).disconnect()
        self.lock.release()

    def start(self, instructions):
        """
        Comienza la simulación dada una lista de instrucciones.

        Parameters
        ----------
        instructions : List[Instruction]
            Lista de instrucciones a ejecutar en la simulación.
        """

        self.instructions = instructions.sort(key=lambda i: i.time)
        GLOBAL_TIMER.start()
        if not self.instructions:
            return

        for i in self.instructions:
            i.set_simulation(self)
            i.start()

    def join(self):
        [i.join() for i in self.instructions]

    def _get_port_by_name(self, port_name) -> Port:
        return self.ports[port_name]

    def _get_host_by_name(self, host_name) -> Host:
        return self.devices[host_name]