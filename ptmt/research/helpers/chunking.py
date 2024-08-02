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

import typing

_T = typing.TypeVar('_T')
_K = typing.TypeVar('_K')

def chunk_by(key: typing.Callable[[_T], _K], it: typing.Iterable[_T]) -> typing.Iterator[tuple[_K, list[_T]]]:
    ite = iter(it)
    try:
        value = next(ite)
        current = [value]
        current_key = key(value)
        for value in ite:
            k = key(value)
            if k == current_key:
                current.append(value)
            else:
                yield current_key, current
                current = [value]
                current_key = k
        yield current_key, current
    except StopIteration:
        pass
