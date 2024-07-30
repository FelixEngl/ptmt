from typing import Callable, Union, Optional, Any, Protocol

from ptmt.dictionary_readers.v1.readers.dicts import DictReaderBase, ParserParam
from ptmt.dictionary_readers.v1.readers.linetree import LineTree
from ptmt.dictionary_readers.v1.readers.transformer import ColumnContentType

ToIgnoreFunction = Callable[[Any], bool]
ConverterCallable = Union[
    Callable[[ColumnContentType], LineTree],
    Callable[[ColumnContentType, Optional[ToIgnoreFunction]], LineTree]
]


class DictReaderCreatorParam(Protocol):
    def __call__(self, parser: ParserParam, *args: Any, **kwargs) -> DictReaderBase: ...
