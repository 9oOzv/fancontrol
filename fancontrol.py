#!/usr/bin/env python3

from pathlib import Path
from time import time, sleep

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

class Fan:
    
    hwmon_name: str | None = None
    pwm_index: int | None = None
    path: Path | None = None

    def __init__(
        self,
        name: str,
        hwmon_name: str | None = None,
        pwm_index: int | None = None,
        pwm_path: str | Path = None
    ):
        self.name = name
        if pwm_path is not None:
            path = Path(pwm_path)
            if not path.exists():
                raise FileNotFoundError(f'Cannot find PWM {pwm_path}')
            self.path = path
        elif hwmon_name and pwm_index:
            self.hwmon_name = hwmon_name
            self.pwm_index = pwm_index
            self.resolve_path()
        else:
            self.path = None

    def resolve_path(self):
        if self.path: return
        for name_path in Path('/sys/class/hwmon').glob('hwmon*/name'):
            with open(name_path) as f:
                iname = f.read().strip()
            if iname != self.hwmon_name:
                continue
            path = name_path.parent / f'pwm{self.pwm_index}'
            if not path.exists():
                continue
            self.path = path
            print(f'Found PWM for `{self.name}`: {path}')
            return
        raise FileNotFoundError(f'Cannot find PWM {self.hwmon_name} {self.pwm_index}')

    def set(self, percent: float):
        print(f'{self.name}: Setting speed to {percent}%')
        en = f'{self.path}_enable'
        with open(en, 'w') as f:
            f.write('1')
        with open(self.path, 'w') as f:
            f.write(str(int(percent / 100.0 * 255)))

class MultiFan:

    def __init__(
        self,
        name: str,
        fans: list[Fan],
    ):
        self.name = name
        self.fans = fans

    def set(self, value: int):
        for fan in self.fans:
            fan.set(value)


class Point:

    def __init__(
        self,
        temp: float,
        speed: int,
    ):
        self.temp = temp
        self.speed = speed


class Curve:

    def __init__(
        self,
        points: list[Point],
    ):
        self.points = points

    def speed(self, temp: float) -> float:
        for point in reversed(self.points):
            if temp >= point.temp:
                return point.speed
        return self.points[0].speed

class Controller:


    def __init__(
        self,
        name: str,
        sensor: Sensor,
        fan: Fan,
        curve: Curve,
    ):
        self.name = name
        self.sensor = sensor
        self.fan = fan
        self.curve = curve

    def run(self):
        temp = self.sensor.temp()
        speed = self.curve.speed(temp)
        print(f'{self.name}: Temperature {temp}°C')
        print(f'{self.name}: Speed {speed}%')
        self.fan.set(speed)

    def set(self, value: int):
        self.fan.set(value)


c0 = Controller(
    'Controller 0',
    SlowSensor(
        'CPU',
        MaxSensor(
            'CPU',
            [
                Sensor('Tctl', label='Tctl'),
                Sensor('Tccd1', label='Tccd1')
            ],
        ),
        10
    ),
    MultiFan(
        'CPU',
        [
            Fan('Back', hwmon_name='nct6799', pwm_index=1),
            Fan('Top', hwmon_name='nct6799', pwm_index=2),
            Fan('Mid', hwmon_name='nct6799', pwm_index=3),
            Fan('Bottom', hwmon_name='nct6799', pwm_index=4),
        ],
    ),
    Curve([
        Point(60, 5),
        Point(70, 35),
        Point(75, 60),
        Point(80, 100),
    ]),
)


def main():
    try:
        while True:
            c0.run()
            sleep(1)
    except:
        c0.set(70)
        raise

if __name__ == '__main__':
    main()
