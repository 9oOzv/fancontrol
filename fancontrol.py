#!/usr/bin/env python3

from pathlib import Path
from time import time, sleep

class Sensor:

    def __init__(
        self,
        name: str,
        input_path: str | Path,
    ):
        self.name = name
        self.path = Path(input_path)

    def temp(self) -> float:
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

    def __init__(
        self,
        name: str,
        pwm_path: str | Path,
    ):
        self.name = name
        self.path = Path(pwm_path)

    def set(self, percent: float):
        print(f'{self.name}: Setting speed to {percent}%')
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
                Sensor('Tctl', '/sys/class/hwmon/hwmon2/temp1_input'),
                Sensor('Tcctl', '/sys/class/hwmon/hwmon2/temp3_input'),
            ],
        ),
        10
    ),
    MultiFan(
        'CPU',
        [
            Fan('Back', '/sys/class/hwmon/hwmon6/pwm1'),
            Fan('Top', '/sys/class/hwmon/hwmon6/pwm2'),
            Fan('Mid', '/sys/class/hwmon/hwmon6/pwm3'),
            Fan('Bottom', '/sys/class/hwmon/hwmon6/pwm4'),
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
