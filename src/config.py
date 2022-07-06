from pathlib import Path

CONFIG = {
    "signal_time": 10,
    "error_detection": "simple_hash",
    "error_prob": 0.001,
}

_CONFIG_FILE_NAME = "config.txt"


def _set_config_val(key: str, value):
    if key == "signal_time":
        CONFIG[key] = int(value)
    if key in ("error_detection", "error_prob"):
        CONFIG[key] = value


def check_config():
    path = Path(_CONFIG_FILE_NAME)
    if path.exists():
        with open(_CONFIG_FILE_NAME, "r") as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.split()
                _set_config_val(key, value)
    else:
        with open(_CONFIG_FILE_NAME, "w+") as file:
            file.writelines(
                [
                    "signal_time 10\n",
                    "error_detection simple_hash",
                    "error_prob 0.0001",
                ]
            )
