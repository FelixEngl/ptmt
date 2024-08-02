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

from enum import auto
from typing import Optional, Any, Callable


class CallableEnumValue:
    def __init__(self, fkt: Callable[..., Any], value: Optional[Any] = None):
        if value is None:
            value = auto()
        self._value: Any = value
        self._fkt = fkt

    def __hash__(self) -> int:
        return hash(self._value)

    def __call__(self, *args, **kwargs) -> Any:
        return self._fkt(*args, **kwargs)

    def __eq__(self, other):
        return isinstance(other, CallableEnumValue) and self._value == other._value

    def __str__(self):
        return str(self._value)

    @property
    def value(self) -> Callable[..., Any]:
        return self._value
