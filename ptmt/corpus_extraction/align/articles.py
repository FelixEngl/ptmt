import typing
from collections.abc import Sized

from ..categories import Categories


class Article(Sized):

    __slots__ = 'lang', 'categories', 'content', 'is_list', '_supplier', 'tokens'

    lang: str
    categories: tuple[int, ...] | None
    content: str | None
    is_list: bool
    _supplier: Categories | None
    tokens: tuple[str, ...] | None

    def __init__(self, lang: str, categories: tuple[int, ...] | None, content: str | None, is_list: bool, *, supplier: Categories | None = None):
        self.lang = lang
        self.categories = categories
        self.content = content
        self.is_list = is_list
        self._supplier = supplier
        self.tokens = None

    def __getstate__(self):
        return {'ln': self.lang, 'ilst': self.is_list, 'cat': self.categories, 'con': self.content, 'tok': self.tokens}

    def __setstate__(self, state):
        self.lang = state['ln']
        self.categories = state['cat']
        self.content = state['con']
        self.is_list = state['ilst']
        self._supplier = None
        self.tokens = state.get('tok', None)

    def __len__(self) -> int:
        if self.content is None:
            return 0
        return len(self.content)

    @property
    def supplier(self) -> Categories|None:
        return self._supplier

    @supplier.setter
    def supplier(self, supplier: Categories):
        self._supplier = supplier

    @property
    def supplied_categories(self) -> tuple[str | None, ...] | None:
        return None if self._supplier is None else self._supplier.convert_ids(*self.categories)

    def __str__(self):
        cats = self.categories if self._supplier is None else self._supplier.convert_ids(*self.categories)
        return (f"Article("
                f"lang='{self.lang}', "
                f"is_list={self.is_list}, "
                f"categories={repr(cats)}, "
                f"content='{self.content}', "
                f"tokens={repr(self.tokens)}"
                f")")

    def __repr__(self):
        return self.__str__()

    def filter_content(self, processor: typing.Callable[[str], str | None]) -> 'Article':
        self.content = self.content if self.content is None else processor(self.content)
        return self

    def with_new_content(self, new_content: str | None) -> 'Article':
        self.content = new_content
        return self

