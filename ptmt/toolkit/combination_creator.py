import dataclasses
import itertools
import typing
from typing import Iterable, Iterator, Any

from ptmt.toolkit.enums import iter_pseudo_enum


@dataclasses.dataclass(frozen=True)
class Single[A]:
    a: A


@dataclasses.dataclass(frozen=True)
class Alternative[A, B]:
    values: Iterable[A] | Single[A] | type[A]
    alt: B = dataclasses.field(default=None)


def _yield_tuples[T](name: str, values: Iterable[T]) -> Iterator[tuple[str, T]]:
    for v in values:
        yield name, v


def _to_tuples(name: str, values: Iterable[Any] | Alternative[Any, Any] | Single[Any] | type[Any] | None) -> typing.Iterator[tuple[str, Any]]:
    match values:
        case None:
            yield name, None
        case Single(a):
            yield name, a
        case Alternative(a, b):
            yield from itertools.chain(
                _to_tuples(name, a),
                [(name, b)]
            )
        case t if isinstance(t, type):
            if t == bool:
                yield from [(name, False), (name, True)]
            else:
                for x in iter_pseudo_enum(t):
                    yield name, x
        case iterable if isinstance(iterable, Iterable):
            for v in iterable:
                yield name, v
        case unknown:
            raise TypeError(f"The type {type(unknown)} is not supported")


def _estimate_count(values: Iterable[Any] | Alternative[Any, Any] | Single[Any] | type[Any] | None) -> int:
    match values:
        case None:
            return 1
        case Single(_):
            return 1
        case Alternative(a, _):
            return 1 + _estimate_count(a)
        case t if isinstance(t, type):
            if t == bool:
                return 2
            else:
                return len(list(iter_pseudo_enum(t)))
        case iterable if isinstance(iterable, Iterable):
            return len(list(iterable))
        case unknown:
            raise TypeError(f"The type {type(unknown)} is not supported")

def yield_all_configs(**kwargs: Iterable[Any] | Alternative[Any, Any] | Single[Any] | type[Any] | None) -> Iterator[dict[str, Any]]:
    temp = tuple(_to_tuples(name, value) for name, value in kwargs.items())
    for combined in itertools.product(*temp):
        yield dict(combined)


def estimate_count(**kwargs: Iterable[Any] | Alternative[Any, Any] | Single[Any] | type[Any] | None) -> dict[str, int]:
    return {k: _estimate_count(v) for k, v in kwargs.items()}

def calc_combinations_ct(d: dict[str, int]) -> int:
    ct = 1
    for v in d.values():
        ct *= v
    return ct

def estimate_complete_count(**kwargs: Iterable[Any] | Alternative[Any, Any] | Single[Any] | type[Any] | None) -> int:
    return calc_combinations_ct(estimate_count(**kwargs))
