# Copyright 2024 Felix Engl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import functools
import re
import typing

from .debug import DebuggableComponent
from .articles import Article


@typing.runtime_checkable
class ArticleCondition(DebuggableComponent, typing.Protocol):
    @abc.abstractmethod
    def __call__(self, article: Article) -> bool:
        """
        Returns true or false, if the condition is met.
        """
        ...

    def __neg__(self) -> 'ArticleCondition':
        return self.__invert__()

    def __invert__(self) -> 'ArticleCondition':
        return _Not(self)

    def __ior__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        return self.__or__(other)

    # noinspection PyProtectedMember
    def __or__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        if isinstance(self, _Not) and isinstance(other, _Not):
            return _Not(_And(self._underlying, other._underlying))
        return _Or(self, other)

    def __iadd__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        return self.__and__(other)

    # noinspection PyProtectedMember
    def __and__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        if isinstance(self, _Not) and isinstance(other, _Not):
            return _Not(_Or(self._underlying, other._underlying))
        return _And(self, other)

    def __ixor__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        return self.__xor__(other)

    def __xor__(self, other: 'ArticleCondition') -> 'ArticleCondition':
        return _Xor(self, other)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(*)'

    # def debug_desc(self) -> str:
    #     return "CONDITION"


class _Not(ArticleCondition):
    __slots__ = '_underlying'

    # noinspection PyProtocol
    def __init__(self, to_negate: 'ArticleCondition'):
        self._underlying = to_negate

    def __call__(self, article: Article) -> bool:
        return not self._underlying(article)

    def __invert__(self) -> 'ArticleCondition':
        return self._underlying

    def __repr__(self):
        return f'~{repr(self._underlying)}'

    def debug_desc(self) -> str:
        return 'NOT'

    def debug_down(self, depth: int):
        self._underlying.debug_with_depth(depth)


class _LROperator(ArticleCondition):
    __slots__ = '_left', '_right'

    # noinspection PyProtocol
    def __init__(self, left: 'ArticleCondition', right: 'ArticleCondition'):
        self._left = left
        self._right = right

    def debug_down(self, depth: int):
        self._left.debug_with_depth(depth)
        self._right.debug_with_depth(depth)


class _Or(_LROperator):
    def __call__(self, article: Article) -> bool:
        return self._left(article) or self._right(article)

    def __repr__(self):
        return f'({self._left.__repr__()} | {self._right.__repr__()})'

    def debug_desc(self) -> str:
        return 'OR'


class _Xor(_LROperator):
    def __call__(self, article: Article) -> bool:
        return self._left(article) != self._right(article)

    def __invert__(self) -> 'ArticleCondition':
        return _NXor(self._left, self._right)

    def __repr__(self):
        return f'({self._left.__repr__()} ^ {self._right.__repr__()})'

    def debug_desc(self) -> str:
        return 'XOR'


class _NXor(_LROperator):
    def __call__(self, article: Article) -> bool:
        return self._left(article) == self._right(article)

    def __invert__(self) -> 'ArticleCondition':
        return _Xor(self._left, self._right)

    def __repr__(self):
        return f'~({self._left.__repr__()} ^ {self._right.__repr__()})'

    def debug_desc(self) -> str:
        return 'NXOR'


class _And(_LROperator):
    def __call__(self, article: Article) -> bool:
        return self._left(article) and self._right(article)

    def __repr__(self):
        return f'({self._left.__repr__()} & {self._right.__repr__()})'

    def debug_desc(self) -> str:
        return 'AND'


# noinspection PyPep8Naming
class article_condition(ArticleCondition):
    __slots__ = '_func'

    # noinspection PyProtocol
    def __init__(self, func: typing.Callable[[Article], bool]):
        self._func = func
        functools.update_wrapper(self, func)

    def __call__(self, article: Article) -> bool:
        return self._func(article)

    def __repr__(self) -> str:
        return f'{self.__name__}(*)'


@article_condition
def is_not_a_list(art: Article) -> bool:
    return not art.is_list


@article_condition
def is_a_list(art: Article) -> bool:
    return art.is_list


@article_condition
def has_category(art: Article) -> bool:
    return art.categories is not None and len(art.categories) > 0


@article_condition
def has_language(art: Article) -> bool:
    return art.lang is not None and art.lang != ''


@article_condition
def has_content(article: Article) -> bool:
    return article.content is not None and article.content != ''


# noinspection PyPep8Naming
class has_at_least_categories(ArticleCondition):
    __slots__ = '_n'

    # noinspection PyProtocol
    def __init__(self, n: int):
        self._n = n

    def __call__(self, article: Article) -> bool:
        return has_category(article) and len(article.categories) >= self._n

    def __repr__(self):
        return f'({repr(has_category)} & len(*.categories) >= {self._n})'


# noinspection PyPep8Naming
class has_fitting_language(ArticleCondition):

    __slots__ = '_allowed'

    # noinspection PyProtocol
    def __init__(self, *allowed_languages: str):
        self._allowed = set(allowed_languages)

    def __call__(self, article: Article) -> bool:
        return has_language(article) and article.lang in self._allowed

    def __repr__(self):
        return f'({repr(has_language)} & (*.lang in {repr(self._allowed)}))'


# noinspection PyPep8Naming
class has_content_of_length(ArticleCondition):

    __slots__ = '_min_length', "_max_length"

    _illegal_args = ValueError('Needs a has_content_of_length(range), has_content_of_length((x, x)), has_content_of_length(x, x), has_content_of_length(min=x), has_content_of_length(max=x), has_content_of_length(min=x, max=x) as args!')

    # noinspection PyProtocol
    def __init__(
            self,
            min: range | tuple[int | None, int | None] | int | None = None,
            max: int | None = None,
    ):
        if isinstance(min, tuple):
            if max is not None:
                raise has_content_of_length._illegal_args
            min, max = min
        elif isinstance(min, range):
            if max is not None:
                raise has_content_of_length._illegal_args
            max = min.stop
            min = min.start

        if min is None and max is None:
            raise has_content_of_length._illegal_args

        self._min_length = min
        self._max_length = max

    def __call__(self, article: Article) -> bool:

        _len = len(article)

        match self._min_length, self._max_length:
            case None, _max:
                return _len <= _max
            case _min, None:
                return _min <= _len
            case _min, _max:
                return _min <= _len <= _max

        raise ValueError('Illegal State')

    def __repr__(self):
        match self._min_length, self._max_length:
            case None, _max:
                return f'(len(*) <= {_max})'
            case _min, None:
                return f'({_min} <= len(*))'
            case _min, _max:
                return f'({_min} <= len(*) <= {_max})'
        return '(#Illegal-has_content_of_length no min or max)'


# noinspection PyPep8Naming
class content_has_tokens_between(ArticleCondition):

    __slots__ = '_min_length', "_max_length"

    _illegal_args = ValueError('Needs a content_has_at_tokens_between(range), content_has_at_tokens_between((x, x)), content_has_at_tokens_between(x, x), content_has_at_tokens_between(min=x), content_has_at_tokens_between(max=x), content_has_at_tokens_between(min=x, max=x) as args!')

    # noinspection PyProtocol
    def __init__(
            self,
            min: range | tuple[int | None, int | None] | int | None = None,
            max: int | None = None,
    ):
        if isinstance(min, tuple):
            if max is not None:
                raise content_has_tokens_between._illegal_args
            min, max = min
        elif isinstance(min, range):
            if max is not None:
                raise content_has_tokens_between._illegal_args
            max = min.stop
            min = min.start

        if min is None and max is None:
            raise content_has_tokens_between._illegal_args

        self._min_length = min
        self._max_length = max

    def __call__(self, article: Article) -> bool:

        _len = article.content.count(' ')

        match self._min_length, self._max_length:
            case None, _max:
                return _len <= _max
            case _min, None:
                return _min <= _len
            case _min, _max:
                return _min <= _len <= _max

        raise ValueError('Illegal State')

    def __repr__(self):
        match self._min_length, self._max_length:
            case None, _max:
                return f'(len(*.tokens) <= {_max})'
            case _min, None:
                return f'({_min} <= len(*.tokens))'
            case _min, _max:
                return f'({_min} <= len(*.tokens) <= {_max})'
        return '(#Illegal-has_content_of_length no min or max)'


# noinspection PyPep8Naming
class matches(ArticleCondition):

    __slots__ = '_pattern'

    # noinspection PyProtocol
    def __init__(self, pattern: str | typing.Pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._pattern = pattern

    def __call__(self, article: Article) -> bool:
        return has_content(article) and self._pattern.search(article.content) is not None

    def __repr__(self):
        return f"({repr(has_content)} & '{self._pattern.pattern}'.search(*.content))"
