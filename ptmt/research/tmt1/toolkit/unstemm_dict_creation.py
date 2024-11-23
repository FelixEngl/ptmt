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

import operator
from collections import defaultdict
from os import PathLike
from pathlib import Path

import jsonpickle
from ldatranslate import PyDictionary, LanguageHint, PyDictionaryEntry

from ptmt.research.dirs import DataDirectory
from ptmt.research.tmt1.toolkit.data_creator import TokenizedValue


def create_unstemm_dictionary(
        language: LanguageHint | str,
        source_file: Path | str | PathLike,
        paper_dir: DataDirectory
) -> PyDictionary:
    root = paper_dir.deepl_path()
    root.mkdir(exist_ok=True, parents=True)
    path_to_dict = root / "unstem_dict.dict"
    if path_to_dict.exists():
        return PyDictionary.load(path_to_dict)
    language = language if isinstance(language, str) else str(language)
    new_dictionary = PyDictionary(str(language) + "_o", str(language) + "_p")
    source_file = source_file if isinstance(source_file, Path) else Path(source_file)
    filtered_words = defaultdict(lambda: defaultdict(lambda: 0))
    with source_file.open("r", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
        for line in f:
            data: TokenizedValue = jsonpickle.loads(line)
            targ = data.entries[language]
            for o, p in zip(targ.origin, targ.tokenized):
                filtered_words[o][p] += 1
    for o, value in filtered_words.items():
        p, ct = max(value.items(), key=operator.itemgetter(1))
        entry = PyDictionaryEntry(o, p)
        entry.set_meta_a_value(str(ct))
        new_dictionary.add(entry)
    new_dictionary.save(path_to_dict)
    return new_dictionary

