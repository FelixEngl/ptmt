from collections import defaultdict
from os import PathLike
from pathlib import Path

import jsonpickle
from ldatranslate.ldatranslate import LanguageHint

from ptmt.research.tmt1.toolkit.data_creator import TokenizedValue


def load_test_data(
        test_data: Path | PathLike | str,
        limit: int | None,
        *languages: LanguageHint | str
) -> dict[str, list[tuple[int, list[str]]]]:
    test_data = Path(test_data)
    languages = tuple(str(x if not isinstance(x, str) else LanguageHint(x)) for x in languages)
    loaded_data = []
    with test_data.open("r", encoding="UTF-8") as inp:

        for value in inp:
            dat: TokenizedValue = jsonpickle.loads(value)

            loaded_data.append((dat.id, {value: dat.entries[value].tokenized for value in languages}))

    if limit is not None:
        loaded_data.sort(key=lambda x: x[0])
        loaded_data = loaded_data[:limit]
        print(f'Limited to {len(loaded_data)}')

    result = defaultdict(list)

    for id, entries in loaded_data:
        for k, v in entries.items():
            result[k].append((id, v))
    del loaded_data

    return dict(result)

