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

import functools
import typing
from os import PathLike
from pathlib import Path
from typing import Callable

import jsonpickle
from ldatranslate import PyDictionary, SolvedMetadata, translate_topic_model

from ptmt.research.dirs import DataDirectory
from ptmt.research.lda_model import create_ratings
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.toolkit.data_creator import TokenizedValue

_DICTIONARY_FILTER = Callable[[str, SolvedMetadata | None], bool]
SINGLE_FILTER = tuple[_DICTIONARY_FILTER, _DICTIONARY_FILTER]


def _filter_iate_and_msterms_wrapper(f: Callable[[str, SolvedMetadata | None], bool]) -> _DICTIONARY_FILTER:
    @functools.wraps(f)
    def wrapper(word: str, meta: SolvedMetadata | None) -> bool:
        if meta is not None:
            assoc = meta.associated_dictionaries
            if len(assoc) == 1:
                return assoc[0] != "IATE" and assoc[0] != "ms_terms"
            if len(assoc) == 2:
                return all(x == "IATE" or x == "ms_terms" for x in assoc)
        return f(word, meta)

    return wrapper


def translate_models(
        lang_a: str,
        lang_b: str,
        out_dir: DataDirectory,
        dictionary: PyDictionary | Path | PathLike | str,
        test_data: Path | PathLike | str,
        limit: int | None,
        filters: tuple[SINGLE_FILTER, SINGLE_FILTER] | None,
        configs: typing.Iterable[TranslationConfig] | Callable[[], typing.Iterable[TranslationConfig]]
):
    if callable(configs):
        my_configs = configs()
    else:
        my_configs = configs

    finished_count = 0

    for config in my_configs:
        targ = out_dir.load_single(config.config_id)
        if targ.model_path.exists():
            finished_count += 1
            continue

    if finished_count == len(my_configs):
        print(f"Everything is already translated!")
        return


    if filters is None:
        def _default(_word: str, _meta: SolvedMetadata | None) -> bool:
            return True
        filters = (_default, _default), (_filter_iate_and_msterms_wrapper(_default), _filter_iate_and_msterms_wrapper(_default))
    else:
        filters = filters[0], tuple(_filter_iate_and_msterms_wrapper(value) for value in filters[1])

    d1: PyDictionary = (dictionary if isinstance(dictionary, PyDictionary) else PyDictionary.load(dictionary)).filter(*filters[0])
    d2: PyDictionary = d1.filter(*filters[1])

    original_model, topic_model = out_dir.load_original_models()

    test_data = Path(test_data)
    loaded_data = []
    with test_data.open("r", encoding="UTF-8") as inp:
        l_a = str(lang_a)
        l_b = str(lang_b)
        for value in inp:
            dat: TokenizedValue = jsonpickle.loads(value)
            loaded_data.append((dat.id, dat.entries[l_a].tokenized, dat.entries[l_b].tokenized))

    if limit is not None:
        loaded_data.sort(key=lambda x: x[0])
        loaded_data = loaded_data[:limit]
        print(f'Limited to {len(loaded_data)}')
    a_data = []
    b_data = []
    for entry in loaded_data:
        a_data.append((entry[0], entry[1]))
        b_data.append((entry[0], entry[2]))
    del loaded_data
    assert a_data is not None and len(a_data) > 0
    assert b_data is not None and len(b_data) > 0

    a_ratings = create_ratings(topic_model, original_model.alpha, 0.01, a_data)

    with open(out_dir.translation_rating_path(), "w") as f:
        f.write(jsonpickle.dumps(a_ratings))

    for config in my_configs:
        print(f"Translate: {config.config_id}")
        targ = out_dir.load_single(config.config_id)

        if targ.model_path.exists():
            print(f"{config.config_id} already translated. Skipping!")
            continue


        config.alpha = original_model.alpha
        cfg = config.to_translation_config()
        if config.limited_dictionary:
            d = d2
        else:
            d = d1

        translated = translate_topic_model(topic_model, d, config.voting, cfg)

        config_pickle = jsonpickle.dumps(config)
        cfg_json = targ.config_path
        cfg_json.write_text(config_pickle)
        translated.save_binary(targ.model_path)
        translated.show_top(10)
        b_ratings = create_ratings(translated, original_model.alpha, 0.01, b_data)
        assert len(b_ratings) == len(b_data)
        targ.rating_path.write_text(jsonpickle.dumps(b_ratings))
    print("Finished translating!")

