from pathlib import Path

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
