import enum
import typing


_E = typing.TypeVar('_E', bound=type[enum.Enum])
_EIter = typing.TypeVar('_EIter')
_T = typing.TypeVar('_T')
_K = typing.TypeVar('_K')
_VT_co = typing.TypeVar("_VT_co", covariant=True)


class MappingAccess:
    __MAP__: dict[typing.Any, typing.Any]

    @classmethod
    def value_for(cls: type[_EIter], key: typing.Any) -> _EIter:
        if isinstance(key, cls) and key in cls:
            return key
        return cls.__MAP__[key]


def mapping_type(enum_cls: type[_EIter]) -> type[_EIter] | MappingAccess:
    enum_cls.__bases__ = enum_cls.__bases__ + (MappingAccess, )
    enum_cls: type[_EIter] | MappingAccess
    enum_cls.__MAP__ = dict()
    return enum_cls


# x: typing.Callable[[_E], _E | MappingAccess]

class enum_mapper:
    def __init__(self, process: typing.Callable[[_K], typing.Any]):
        self._pog = process

    def wrap(self, cls: type[_EIter]) -> type[_EIter] | MappingAccess:
        cls = mapping_type(cls)
        for x in cls:
            cls.__MAP__[self._pog(x)] = x
        return cls


# @enum_mapper(lambda x: x.value[0]).wrap
# class TimeUnit(enum.Enum):
#     Nanoseconds = ('ns', 1)
#     Seconds = ('s', 1E+9)
#     Minutes = ('m', 6E+10)
#
#
# if __name__ == '__main__':
#     print(TimeUnit.Minutes)
#     print(TimeUnit.value_for('ns'))
