import typing

_T = typing.TypeVar('_T')
_K = typing.TypeVar('_K')

def chunk_by(key: typing.Callable[[_T], _K], it: typing.Iterable[_T]) -> typing.Iterator[tuple[_K, list[_T]]]:
    ite = iter(it)
    try:
        value = next(ite)
        current = [value]
        current_key = key(value)
        for value in ite:
            k = key(value)
            if k == current_key:
                current.append(value)
            else:
                yield current_key, current
                current = [value]
                current_key = k
        yield current_key, current
    except StopIteration:
        pass
