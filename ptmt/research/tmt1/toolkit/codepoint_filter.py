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

import unicodedata

_illegal_codepoints = ("P", "S", "Z", "C", "M")


def is_illegal_char(word: str) -> bool:
    """Filter for illegal codepoints"""
    if len(word) == 1:
        category = unicodedata.category(word)
        return category[0] in _illegal_codepoints
    return False
