
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
