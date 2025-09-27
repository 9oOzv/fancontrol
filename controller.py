from sensor import Sensor, MaxSensor, SlowSensor
from fan import Fan, MultiFan
from curve import Curve, Point

class Controller:


    def __init__(
        self,
        name: str,
        sensor: Sensor,
        fan: Fan,
        curve: Curve,
        fallback_speed: int = 100,
    ):
        self.name = name
        self.sensor = sensor
        self.fan = fan
        self.curve = curve
        self.fallback_speed = fallback_speed

    def run(self):
        temp = self.sensor.temp()
        speed = self.curve.speed(temp)
        print(f'{self.name}: Temperature {temp}°C')
        print(f'{self.name}: Speed {speed}%')
        self.fan.set(speed)

    def set(self, value: int):
        self.fan.set(value)

    def fallback(self):
        print(f'{self.name}: Fallback speed {self.fallback_speed}%')
        self.fan.set(self.fallback_speed)


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
