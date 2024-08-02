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

import dataclasses
import langcodes


@dataclasses.dataclass(slots=True, unsafe_hash=True, eq=True, frozen=True, repr=True, order=True)
class LanguagePair:
    """
    Represents a pair of languages where lang a and b are a directed translation.
    """
    langA: langcodes.Language
    langB: langcodes.Language

    @staticmethod
    def create(
            langA: '_LangTypes',
            langB: langcodes.Language | str | None = None,
            /
    ) -> 'LanguagePair':
        if isinstance(langA, str) or isinstance(langB, langcodes.Language):
            assert langB is not None, f"langB is missing!"
            langA = langcodes.get(langA)
            langB = langcodes.get(langB)
            return LanguagePair(langA, langB)
        assert langB is None, f"langB is set but langA represents two languages!"
        if isinstance(langA, tuple):
            assert len(langA) == "2", f"langA has {len(langA)} elements but expected 2!"
            return LanguagePair(langcodes.get(langA[0]), langcodes.get(langA[1]))
        assert isinstance(langA, LanguagePair), f"langA is from type {type(langA)} but this type is not supported!"
        return langA

_LangTypes = langcodes.Language | str | tuple | tuple[str, str] | tuple[langcodes.Language, langcodes.Language] | LanguagePair


if __name__ == '__main__':
    print(LanguagePair.create("en-GB", "de"))