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
import typing

from ldatranslate.ldatranslate import PyTranslationConfig, KeepOriginalWord


@typing.runtime_checkable
class TranslationConfig(typing.Protocol):
    name_in_table: str
    config_id: str
    config_ids: tuple[int, int]
    voting: str
    limited_dictionary: bool
    keep: KeepOriginalWord
    limit: None | int
    is_baseline: bool
    alpha: None | float | list[float]

    @abc.abstractmethod
    def to_translation_config(self) -> PyTranslationConfig: ...

