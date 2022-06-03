from .port_device import PortDevice
from datalink_layer.frame import Frame


class Switch(PortDevice):
    """Representa un switch en la simulación."""

    def on_frame_received(self, frame: Frame, port: int) -> None:
        print(
            f'[{self.sim_time:>6}] {self.name + " - " + str(port):>18}  received: {frame}'
        )
        self.mac_table[frame.from_mac] = self.port_name(port)

        if frame.to_mac == 65_535 or frame.to_mac not in self.mac_table:
            self.broadcast(self.port_name(port), [frame.bit_data])
        else:
            self.ports[self.mac_table[frame.to_mac]].send([frame.bit_data])
        self.ports_buffer[port - 1] = []
