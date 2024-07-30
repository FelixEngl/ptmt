import itertools
import typing
from os import PathLike
from pathlib import Path
from typing import Iterator

import jsonpickle

from .aligned_articles import AlignedArticles


@typing.runtime_checkable
class AlignedArticleReader(typing.Iterable[AlignedArticles], typing.Protocol):

    def __or__(self, other: 'AlignedArticleReader') -> 'AlignedArticleReader':
        return _AlignedArticleReaderSequence(self, other)

    def __add__(self, other: 'AlignedArticleReader') -> 'AlignedArticleReader':
        return self.__or__(other)


# noinspection PyPep8Naming
class read_aligned_articles(AlignedArticleReader):

    _source: typing.Iterable[AlignedArticles]
    _buffer: int | None
    __slots__ = '_source', '_buffer'

    @staticmethod
    def _aa_read_build_from_textio(f: typing.TextIO, repair: bool = False) -> typing.Iterator[AlignedArticles]:
        while True:
            tmp = f.readline()
            if tmp == '':
                break
            if repair:
                tmp = tmp.replace('"py/object": "toolkit.',
                                  '"py/object": "toolkit.')
            curr = jsonpickle.loads(tmp)
            assert isinstance(curr, AlignedArticles)
            yield curr

    @staticmethod
    def _aa_read_bulk(path: str | PathLike[str], repair: bool = False) -> typing.Iterator[AlignedArticles]:
        with open(path, 'r', encoding='UTF-8') as f:
            yield from read_aligned_articles._aa_read_build_from_textio(f, repair)

    def __init__(
            self,
            source: str | PathLike[str] | Path | typing.TextIO | typing.Iterable[AlignedArticles] | AlignedArticleReader,
            buffer: int | None = None
    ):
        self._buffer = buffer
        if isinstance(source, Path) or isinstance(source, str):
            self._source = read_aligned_articles._aa_read_bulk(source, True)
        elif isinstance(source, typing.TextIO):
            self._source = read_aligned_articles._aa_read_build_from_textio(source)
        elif isinstance(source, PathLike):
            self._source = read_aligned_articles._aa_read_bulk(source, True)
        else:
            self._source = source

    def __iter__(self) -> typing.Iterator[AlignedArticles]:
        if self._buffer:
            for value in itertools.batched(self._source, self._buffer):
                yield from value
        else:
            yield from self._source


def read_multiple_aligned_articles(
        *to_read: str | PathLike[str] | Path | typing.TextIO | typing.Iterable[AlignedArticles] | AlignedArticleReader
) -> AlignedArticleReader:
    return _AlignedArticleReaderSequence(*[read_aligned_articles(x) for x in to_read])


class _AlignedArticleReaderSequence(AlignedArticleReader):
    _underlying: list[AlignedArticleReader]
    __slots__ = '_underlying'

    def __init__(self, *other: AlignedArticleReader):
        self._underlying = []
        for x in other:
            if isinstance(x, _AlignedArticleReaderSequence):
                self._underlying.extend(x._underlying)
            else:
                self._underlying.append(x)

    def __iter__(self) -> Iterator[AlignedArticles]:
        return itertools.chain(*self._underlying)

