import itertools
from typing import Iterable, TypeVar, Iterator, Tuple

T = TypeVar('T')


def chunked_iterable(iterable: Iterable[T], size: int) -> Iterator[Tuple[T]]:
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

