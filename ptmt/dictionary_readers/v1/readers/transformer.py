import abc
from abc import ABC
from dataclasses import dataclass
from typing import Tuple, Union, List, Any

from lark import Transformer


@dataclass(repr=False)
class BaseTokenClass(ABC):
    value: Any

    @property
    @abc.abstractmethod
    def _tag(self) -> str:
        ...

    def __repr__(self):
        return f"{'{'}{self._tag}~{repr(self.value)}{'}'}"



@dataclass(repr=False)
class Generic(BaseTokenClass):
    value: Union[str, List[Any]]

    @property
    def _tag(self) -> str:
        return "generic"


@dataclass(repr=False)
class Separator(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "sep"

    def __hash__(self):
        return hash(self.value)


@dataclass(repr=False)
class LetterLike(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "letter"


@dataclass(repr=False)
class SpecialCharacter(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "s_char"


@dataclass(repr=False)
class SpecialWords(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "s_word"


@dataclass(repr=False)
class Punctuation(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "pct"

    def __hash__(self):
        print(self.value)
        return hash(self.value)


@dataclass(repr=False)
class BaseInfoTokenClass(BaseTokenClass):
    pass


@dataclass(repr=False)
class AdditionalInfo(BaseInfoTokenClass):
    value: List[Any]

    @property
    def _tag(self) -> str:
        return "infoAdditional"

    def __hash__(self):
        return hash(tuple(self.value))


@dataclass(repr=False)
class TopicInfo(BaseInfoTokenClass):
    value: List[Any]

    @property
    def _tag(self) -> str:
        return "infoTopic"


@dataclass(repr=False)
class ReferenceInfo(BaseInfoTokenClass):
    value: List[Any]

    @property
    def _tag(self) -> str:
        return "infoReference"


@dataclass(repr=False)
class MetaInfo(BaseInfoTokenClass):
    value: List[Any]

    @property
    def _tag(self) -> str:
        return "infoMeta"


@dataclass(repr=False)
class MiscellaneousSymbol(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "micsSymbol"


@dataclass(repr=False)
class ColumnSeparator(BaseTokenClass):
    value: str

    @property
    def _tag(self) -> str:
        return "sepCol"


class ClassedTuple(tuple):
    def __repr__(self):
        return f"T{super().__repr__()}"


class Column(ClassedTuple):
    def __repr__(self):
        return f"C{super().__repr__()}"


class ColumnContent(ClassedTuple):
    def __repr__(self):
        return f"CC{super().__repr__()}"


class SeparatedContent(ClassedTuple):

    def __repr__(self):
        return f"SC{super().__repr__()}"


SeparatedContentType = Tuple[Union[str, BaseTokenClass], ...]
ColumnContentType = Tuple[SeparatedContentType, ...]
ColumnType = Tuple[ColumnContentType, ...]
TransformedParsedLine = Tuple[ColumnType, ...]


# noinspection PyMethodMayBeStatic,PyPep8Naming
class LineTransformer(Transformer):

    def start(self, content):
        return tuple(content)

    def column(self, content):
        return Column(content)

    def column_content(self, content):
        return ColumnContent(content)

    def content_separated_content(self, content):
        return SeparatedContent(content)

    def DICT_WORD(self, content):
        return content.value

    def SPECIAL_CHARACTER(self, content):
        return content.value

    def SPECIAL_WORD(self, content):
        return content.value

    def UNICODE_MISCELLANEOUS_SYMBOLS(self, content):
        return content.value

    def COLUMN_SEPARATOR(self, content):
        (s,) = content
        return ColumnSeparator(s)

    def word(self, content):
        return ''.join(content)

    def SEPARATOR(self, content):
        return content.value

    def separator(self, content):
        s, = content
        return Separator(s)

    def addition_info(self, content):
        return AdditionalInfo(content)

    def topic_info(self, content):
        return TopicInfo(content)

    def meta_info(self, content):
        return MetaInfo(content)

    def reference_info(self, content):
        return ReferenceInfo(content)

    def punctuation(self, content):
        # assert not isinstance(content, list)
        return Punctuation(content)

    def letter_like(self, content):
        return LetterLike(content)

    def special_word(self, content):
        return SpecialWords(content)

    def special_character(self, content):
        (s,) = content
        return SpecialCharacter(s)

    def html_encoded(self, content):
        return ''.join(content)

    def value(self, content):
        (s,) = content
        return s

    def value_info(self, content):
        (s, ) = content
        return s

    def miscellaneous_symbols(self, content):
        (s,) = content
        return MiscellaneousSymbol(s)
