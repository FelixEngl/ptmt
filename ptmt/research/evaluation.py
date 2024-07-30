import logging
import typing
from collections import defaultdict

import numpy
import numpy as np
from ptmt.research.dirs import Rating


def _dicount(n: int) -> numpy.ndarray:
    return numpy.ones(n) / numpy.log2(numpy.arange(n, dtype=numpy.float_) + 2)


def _dg(target: list[int | float] | numpy.ndarray) -> numpy.ndarray:
    if not isinstance(target, numpy.ndarray):
        target = numpy.array(target)
    return target * _dicount(len(target))


def _c(target: list[int | float] | numpy.ndarray) -> numpy.ndarray:
    return numpy.cumsum(target)


def _dcg(target: list[int | float] | numpy.ndarray) -> numpy.ndarray:
    if not isinstance(target, numpy.ndarray):
        target = numpy.array(target)
    return _c(_dg(target))


def _ndcg(ideal: list[int | float] | numpy.ndarray, target: list[int | float] | numpy.ndarray) -> numpy.ndarray:
    assert len(ideal) == len(target), "Ideal and target do not have the same length!"
    return _dcg(target) / _dcg(ideal)


_T = typing.TypeVar('_T')
_K = typing.TypeVar('_K')


@typing.runtime_checkable
class SupportsGetter(typing.Protocol[_T]):
    def __len__(self) -> _T:...
    def __getitem__(self, item: _T) -> float | int:...


def calculate_ndcg_single(
        ideal: list[_T] | numpy.ndarray,
        target: list[_T] | numpy.ndarray,
        relevance: typing.Mapping[_T, float | int] | SupportsGetter[_T] | typing.Callable[[_T], float | int | None],
        default: int | float | None = None
) -> numpy.ndarray:
    """
    Calculates the NDCG for a provided target based on the ideal.
    The relevance is either provided by a method or some kind of mapping or anything else that supports an access like syntax.
    If default is not set it can fall back to the smallest value in relevance, if it is something like a dict or list.
    Fails if default is none and relevance somehow returns a None for a provided value.
    """

    if isinstance(relevance, typing.Mapping):
        tmp = relevance
        if isinstance(tmp, defaultdict):
            relevance = lambda x: tmp[x]
        else:
            if default is None:
                default = min(tmp.values())
                logging.warning(f"No default value set, falling back to min value in mapping: {default}")
            def inner1(c: _T) -> float | int | None:
                nonlocal tmp, default
                return tmp.get(c, default)
            relevance = inner1
    elif isinstance(relevance, SupportsGetter):
        tmp = relevance
        if default is None:
            if isinstance(tmp, typing.Iterable):
                min_value = min(tmp)
            else:
                min_value = None
                for x in range(len(ideal)):
                    if min_value is None:
                        min_value = x
                    else:
                        min_value = min(min_value, x)
            default = min_value
            logging.warning(f"No default value set, falling back to min value in mapping: {default}")
        def inner2(c: _T) -> float | int:
            nonlocal tmp, default
            if len(tmp) <= c:
                return default
            return tmp[c]
        relevance = inner2

    def relevance_inner(c: _T) -> float | int:
        nonlocal relevance, default
        if (r := relevance(c)) is not None:
            return r
        else:
            assert default is not None, "Default is none but result also returns none!"
            return default

    ideal = np.fromiter((relevance_inner(x) for x in ideal), numpy.float_)
    target = np.fromiter((relevance_inner(x) for x in target), numpy.float_)
    return _ndcg(ideal, target)


RELEVANCE_TYPE = typing.Mapping[_T, float | int] | SupportsGetter[_T] | typing.Callable[[_T], float | int | None]


def calculate_ndcg(
        ideals: typing.Mapping[_K, list[_T] | numpy.ndarray] | list[_T] | numpy.ndarray,
        targets: dict[_K, list[_T] | numpy.ndarray] | tuple[int, list[_T] | numpy.ndarray],
        relevance: dict[_K, RELEVANCE_TYPE] | RELEVANCE_TYPE,
        default: int | float | None = None
) -> tuple[dict[_K, tuple[list[float], None | dict[_K, int | float]]], list[_K] | None, list[_K] | None]:
    """
    Returns a tuple where:
    0: A dict between the associated key and the ndcg value
    1: the missed ideals
    2: the missed targets
    """
    result = dict()
    missed_targets = None
    missed_ideals = None

    if isinstance(targets, tuple):
        targets = {
            targets[0]: targets[1]
        }

    if isinstance(ideals, typing.Mapping):
        missed_targets = list()
        for k, target in targets.items():
            if (i := ideals.get(k)) is not None:
                if isinstance(relevance, dict) and (found := relevance.get(k)) is not None:
                    if found is not None and (isinstance(found, float) or isinstance(found, int)):
                        r = relevance
                        rval = dict(r)
                    else:
                        r = found
                        if isinstance(r, typing.Mapping):
                            rval = dict(r)
                        elif isinstance(r, list):
                            rval = r
                        elif isinstance(r, numpy.ndarray):
                            rval = r.tolist()
                        else:
                            rval = None
                elif isinstance(relevance, list):
                    r = relevance
                    rval = relevance
                elif isinstance(relevance, numpy.ndarray):
                    r = relevance
                    rval = relevance.tolist()
                else:
                    r = relevance
                    rval = None
                r2 = calculate_ndcg_single(i, target, r, default)

                result[k] = r2.tolist(), rval
            else:
                missed_targets.append(k)

        if len(missed_targets) == 0:
            missed_targets = None

        missed_ideals = ideals.keys() - targets.keys()
        if len(missed_ideals) == 0:
            missed_ideals = None
        else:
            missed_ideals = list(missed_ideals)
    else:
        if not isinstance(ideals, numpy.ndarray):
            ideals = numpy.array(ideals)
        for k, target in targets.items():
            if isinstance(relevance, dict) and (found := relevance.get(k)) is not None:
                if found is not None and (isinstance(found, float) or isinstance(found, int)):
                    r = relevance
                    rval = dict(r)
                else:
                    r = found
                    if isinstance(r, typing.Mapping):
                        rval = dict(r)
                    elif isinstance(r, list):
                        rval = r
                    elif isinstance(r, numpy.ndarray):
                        rval = r.tolist()
                    else:
                        rval = None
            elif isinstance(relevance, list):
                r = relevance
                rval = relevance
            elif isinstance(relevance, numpy.ndarray):
                r = relevance
                rval = relevance.tolist()
            else:
                r = relevance
                rval = None
            result[k] = calculate_ndcg_single(ideals, target, r, default), rval

    return result, missed_ideals, missed_targets


def rating_to_doc_id_to_ranking(rating: Rating) -> dict[int, list[int]]:
    return dict(
        (doc_id, list(topic_id for topic_id, _prob in sorted(ideal, key=lambda x: x[1], reverse=True)))
        for doc_id, ideal in rating
    )


def _rating_to_doc_id_to_ranking_with_prob(rating: Rating) -> dict[int, list[tuple[int, float]]]:
    return dict(
        (doc_id, list((topic_id, prob) for topic_id, prob in sorted(ideal, key=lambda x: x[1], reverse=True)))
        for doc_id, ideal in rating
    )


