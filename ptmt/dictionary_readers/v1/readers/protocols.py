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
