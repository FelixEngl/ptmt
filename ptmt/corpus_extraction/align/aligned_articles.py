import typing
from collections.abc import Iterable, Sized
import jsonpickle

from .articles import Article
# noinspection PyUnresolvedReferences
from ..categories import CategorySupplier, Categories
from .conditions import ArticleCondition


class AlignedArticles(Iterable[Article], Sized):

    __slots__ = 'article_id', 'articles', '_supplier'

    def __init__(self, article_id: int, *articles: Article):
        self.article_id: int = article_id
        self.articles: dict[str, Article] = dict()
        for art in articles:
            if art.lang in self.articles:
                raise KeyError(f"The key '{art.lang}' is already in use!")
            self.articles[art.lang] = art
        self._supplier: CategorySupplier | None = None

    @property
    def langs(self) -> typing.Collection[str]:
        return self.articles.keys()

    def __getstate__(self):
        return {'id': self.article_id, 'art': self.articles}

    def __setstate__(self, state):
        self.article_id = state['id']
        self.articles = state['art']
        self._supplier = None

    @property
    def supplier(self) -> CategorySupplier|None:
        return self._supplier

    @supplier.setter
    def supplier(self, supplier: CategorySupplier):
        self._supplier = supplier
        for k, v in self._supplier:
            found = self.articles.get(k, None)
            if found is not None:
                found.supplier = supplier[k]

    @property
    def is_list(self) -> bool:
        return len(self.articles) != 0 and any(x for x in self.articles.values() if x.is_list)

    def __repr__(self):
        return f'AlignedArticles(article_id={self.article_id}, articles={repr(self.articles)})'

    def __str__(self) -> str:
        return f'({self.article_id}, {self.articles})'

    def str_with_token(self):
        return f'({self.article_id}, {self.articles})'

    def any_article_fulfills(self, condition: ArticleCondition) -> bool:
        for x in self.articles.keys():
            if self.article_for_fulfills(x, condition):
                return True
        return False

    def article_for_fulfills(self, lang: str, condition: ArticleCondition) -> bool:
        return condition(self.articles[lang])

    def __len__(self) -> int:
        return len(self.articles)

    def __iter__(self) -> typing.Iterator[Article]:
        yield from self.articles.values()

    def to_json_string(self) -> str:
        return jsonpickle.dumps(self)

    @staticmethod
    def from_json_string(s: str) -> 'AlignedArticles':
        return jsonpickle.loads(s)

    def __getitem__(self, item: str) -> 'Article':
        return self.articles[item]

    def __contains__(self, item: str) -> bool:
        return item in self.articles
