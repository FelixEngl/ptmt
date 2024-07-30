import typing

_T = typing.TypeVar('_T')
def relative_change(target: _T, relative_target: _T) -> _T:
    return (target - relative_target) / relative_target
