import typing
from collections import defaultdict
from collections.abc import Iterable, Sized, Container
from typing import Iterator

import jsonpickle

from ptmt.toolkit.paths import PathObj


class Categories(Iterable[tuple[int, str]], Sized, Container[str | int]):
    __slots__ = "_id2cat", "_cat2id"

    T = typing.TypeVar('T')

    def __init__(self):
        self._id2cat: list[str] = list()
        self._cat2id: dict[str, int] = dict()

    def convert_names(
            self,
            *categories: str,
            method: None | typing.Literal['fail', 'none', 'grow', 'f', 'n', 'g'] = None
    ) -> tuple[int | None, ...]:
        """
        Returns a tuple in the order of categories. May contain None iff method is set to 'none'
        Set one of the flags at method to get some kind of different behaviour. If not set it defaults to 'grow'.
        Methods:
            'grow' | 'g': uses get_or_put on each entry
            'fail' | 'f': throws a KeyError exception if one of the values is not contained
            'none' | 'n': Replaces every missing value with None

        Throws a ValueError is the method is not supported.
        """

        match method:
            case None | 'grow' | 'g':
                return tuple(self.get_or_put(cat) for cat in categories)
            case 'fail' | 'f':
                return tuple(self[cat] for cat in categories)
            case 'none' | 'n':
                return tuple(self.get(cat) for cat in categories)
            case unknown:
                raise ValueError(f"The argument method='{unknown}' is not supported!")

    def convert_ids(self, *category_ids: int, method: None | typing.Literal['fail', 'none', 'f', 'n'] = None) -> tuple[str | None, ...]:
        """
        Returns a tuple in the order of category_ids. May contain None iff method is set to 'none'.
        Set one of the flags at method to get some kind of different behaviour. If not set it defaults to 'none'.
        Methods:
            'fail' | 'f': throws a KeyError exception if one of the values is not contained
            'none' | 'n': Replaces every missing value with None

        Throws a ValueError is the method is not supported.
        """
        match method:
            case None | 'none' | 'n':
                return tuple(self.get(cat_id) for cat_id in category_ids)
            case 'fail' | 'f':
                return tuple(self[cat_id] for cat_id in category_ids)
            case unknown:
                raise ValueError(f"The argument method='{unknown}' is not supported!")

    def get_or_put(self, category: str) -> int:
        found = self._cat2id.get(category, None)
        if found is None:
            idx = len(self._id2cat)
            self._id2cat.append(category)
            self._cat2id[category] = idx
            return idx
        return found

    def get(self, item: str | int, if_not_found: T | None = None) -> str | int | T | None:
        if isinstance(item, str) and item in self._cat2id:
            return self._cat2id[item]
        if item < len(self._id2cat):
            return self._id2cat[item]
        return if_not_found

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            return item in self._cat2id
        if isinstance(item, int):
            return item < len(self._id2cat)
        return False

    def __getitem__(self, item: str | int) -> str | int:
        """
        Throws a KeyError of item not found.
        """
        if isinstance(item, str):
            return self._cat2id[item]
        if item < len(self._id2cat):
            return self._id2cat[item]
        raise KeyError(item)

    def __repr__(self) -> str:
        return f'Categories(id2cat={repr(self._id2cat)}, cat2id={repr(self._cat2id)})'

    def __getstate__(self):
        return {'id2cat': self._id2cat}

    def __setstate__(self, state: dict[str, typing.Any]):
        self._id2cat = state['id2cat']
        self._cat2id = dict((value, i) for i, value in enumerate(self._id2cat))

    def __len__(self):
        return len(self._id2cat)

    def __eq__(self, other):
        return isinstance(other, Categories) and other._id2cat == self._id2cat

    def __iter__(self) -> typing.Iterator[tuple[int, str]]:
        yield from enumerate(self._id2cat)

    def iterate_words(self) -> typing.Iterator[str]:
        yield from self._id2cat


class CategorySupplier(Sized, Container[str | Categories], Iterable[tuple[str, Categories]]):

    T = typing.TypeVar('T')

    def __init__(self):
        self._categories: defaultdict[str, Categories] = defaultdict(Categories)

    @property
    def langs(self) -> set[str]:
        return set(self._categories.keys())

    def __getitem__(self, item: str) -> Categories:
        return self._categories[item]

    def get(self, item: str, if_not_found: T | None) -> Categories | T | None:
        return self._categories.get(item, if_not_found)

    def translate_categories(self, language: str, categories: tuple[str, ...] | None) -> tuple[int, ...] | None:
        if categories is None or len(categories) == 0:
            return None
        return self._categories[language].convert_names(*categories)

    def __getstate__(self):
        return {'categories': dict(self._categories)}

    def __setstate__(self, state):
        self._categories = defaultdict(Categories, state['categories'])

    def __repr__(self):
        s = 'CategorySupplier {'
        for k, v in self._categories.items():
            s += f'{repr(k)}: {len(v)}'
        s += '}'
        return repr(s)

    def __iter__(self) -> Iterator[tuple[str, Categories]]:
        yield from self._categories.items()

    def __len__(self) -> int:
        return len(self._categories)

    def __contains__(self, item) -> bool:
        return item in self._categories

    def save(self, path: PathObj):
        with open(path, "w", encoding='UTF-8') as f:
            f.write(jsonpickle.encode(self))

    @staticmethod
    def load(path: PathObj) -> 'CategorySupplier':
        with open(path, "r", encoding='UTF-8') as f:
            return jsonpickle.decode(f.read().replace('__main__', 'toolkit.categories'))
