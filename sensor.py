from pathlib import Path
from time import time

class Sensor:

    name: str
    label: str | None = None
    path: Path | None = None

    def __init__(
        self,
        name: str,
        label: str | None = None,
        path: str | Path | None = None
    ):
        self.name = name
        if path:
            if not path.exists():
                raise FileNotFoundError(f'Cannot find sensor {path}')
            self.path = Path(path)
        elif label:
            self.label = label
            self.resolve_path()
        else:
            self.path = None

    def resolve_path(self):
        if self.path: return
        for label_path in Path('/sys/class/hwmon').glob('hwmon*/temp*_label'):
            with open(label_path) as f:
                ilabel = f.read().strip()
            if ilabel != self.label:
                continue
            path = label_path.parent / label_path.name.replace('label', 'input')
            if not path.exists():
                continue
            self.path = path
            print(f'Found sensor for `{self.name}`: {path}')
            return
        raise FileNotFoundError(f'Cannot find sensor {self.label}')

    def temp(self) -> float | None:
        if not self.path:
            return None
        with open(self.path) as f:
            return float(f.read()) / 1000


class MaxSensor:
    
    def __init__(
        self,
        name: str,
        sensors: list[Sensor],
    ):
        self.name = name
        self.sensors = sensors

    def temp(self) -> float:
        return max(
            sensor.temp()
            for sensor
            in self.sensors
        )


class AvgSensor:

    def __init__(
        self,
        name: str,
        sensors: list[Sensor],
    ):
        self.name = name
        self.sensors = sensors

    def temp(self) -> float:
        return sum(
            sensor.temp()
            for sensor
            in self.sensors
        ) / len(self.sensors)


class Sample:

    def __init__(
        self,
        temp: float,
        t: float | None = None,
    ):
        self.temp = temp
        self.time = t or time()


class SlowSensor:

    def __init__(
        self,
        name: str,
        sensor: Sensor,
        window_seconds: int,
    ):
        self.name = name
        self.sensor = sensor
        self.seconds = window_seconds
        self.samples = []

    def remvove_old_samples(self):
        for sample in self.samples:
            if sample.time < time() - self.seconds:
                self.samples.remove(sample)

    def temp(self) -> float:
        self.samples.append(
            Sample(self.sensor.temp())
        )
        self.remvove_old_samples()
        return sum(
            sample.temp
            for sample
            in self.samples
        ) / len(self.samples)
