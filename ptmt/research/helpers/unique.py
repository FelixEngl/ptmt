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

_T_co = typing.TypeVar("_T_co", covariant=True)


# noinspection PyPep8Naming
class filter_unique(typing.Iterator[_T_co]):
    def __init__(self, __iterable: typing.Iterable[_T_co], *, key: typing.Callable[[_T_co], typing.Any] | None = None):
        self.__filter = set()
        self.__iterable = iter(__iterable)
        self.__key = key

    def __iter__(self) -> typing.Iterator[_T_co]:
        return self

    def __next__(self) -> _T_co:
        while True:
            value = next(self.__iterable)
            if self.__key is not None:
                k = self.__key(value)
            else:
                k = value
            old_len = len(self.__filter)
            self.__filter.add(k)
            if len(self.__filter) == old_len:
                continue
            return value

