from enum import auto
from typing import Optional, Any, Callable


class CallableEnumValue:
    def __init__(self, fkt: Callable[..., Any], value: Optional[Any] = None):
        if value is None:
            value = auto()
        self._value: Any = value
        self._fkt = fkt

    def __hash__(self) -> int:
        return hash(self._value)

    def __call__(self, *args, **kwargs) -> Any:
        return self._fkt(*args, **kwargs)

    def __eq__(self, other):
        return isinstance(other, CallableEnumValue) and self._value == other._value

    def __str__(self):
        return str(self._value)

    @property
    def value(self) -> Callable[..., Any]:
        return self._value
