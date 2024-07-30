import enum
import time
import typing

from ptmt.toolkit.mappingenum import enum_mapper

TimeLiteral = typing.Literal['ns', 's', 'm']


@enum_mapper(lambda x: x.value[0]).wrap
class TimeUnit(enum.Enum):
    Nanoseconds = ('ns', 1)
    Seconds = ('s', 1E+9)
    Minutes = ('m', 6E+10)


TimeType = TimeUnit | TimeLiteral


class SimpleTimer:
    __slots__ = '_start', '_end', '_unit', '_name'

    def __init__(self, unit: TimeType = TimeUnit.Seconds, name: str | None = None, *, start: bool = False):
        if start:
            self.start()
        else:
            self._start: int | None = None
        self._end: int | None = None
        self._unit: TimeType = unit
        self._name: str | None = name

    def start(self):
        self._start = time.time_ns()

    def stop(self):
        self._end = time.time_ns()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.show()

    def reset(self, unit: TimeType | None = None, name: str | None = None):
        self._start = None
        self._end = None
        self._unit = unit if unit is not None else self._unit
        self._name = name if name is not None else self._name

    def get_measured_time(self, unit: TimeType | None = None) -> int | float:
        assert self._start is not None, 'You have to start the timer'
        assert self._end is not None, 'You have to stop the timer'
        delt = self._end - self._start
        if unit is None:
            unit = self._unit

        found = TimeUnit.value_for(unit)
        return delt / found.value[1]

    def show(self):
        if self._name is None:
            s = f'Measured '
        else:
            s = f'The timer "{self._name}" measured '
        s += f'{self.get_measured_time()}{TimeUnit.value_for(self._unit).value[0]}.'
        print(s)

