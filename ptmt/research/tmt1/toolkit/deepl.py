import typing
from os import PathLike
from pathlib import Path

import jsonpickle
from ldatranslate.ldatranslate import PyDictionary, PyAlignedArticleProcessor, LanguageHint

from ptmt.research.dirs import DataDirectory
from ptmt.research.lda_model import create_ratings
from ptmt.research.tmt1.toolkit.simple_processing import _process_token_list
from ptmt.research.tmt1.toolkit.test_data_load_helper import load_test_data


def deepl_translate(
        original_dictionary: PyDictionary,
        paper_dir: DataDirectory,
        translate_mode: typing.Literal["simple", "complex"],
        processor: PyAlignedArticleProcessor,
        language_hint: LanguageHint | str,
        test_data: Path | PathLike | str,
        limit: int | None,
):
    if (deepl := paper_dir.deepl_if_exists()) is not None and deepl.model_path.exists():
        print("Deepl Translation exists!")
        return
    model = paper_dir.load_original_py_model()
    lang = model.vocabulary().language
    o_lang, p_lang = str(lang) + "_o", str(lang) + "_p"
    a, b = original_dictionary.translation_direction

    if str(a) == o_lang:
        assert str(b) == p_lang
        original_dictionary = original_dictionary.switch_a_to_b()
    else:
        assert str(b) == o_lang
        assert str(a) == p_lang
    deep_path = paper_dir.deepl_path()
    deep_path.mkdir(parents=True, exist_ok=True)
    deepl_path_structure = deep_path / f"mapping_{translate_mode}.json"
    deepl_to_translate_path = deep_path / "to_translate"
    deepl_to_translate_path.mkdir(exist_ok=True)
    result_folder = deep_path / f"translated_{translate_mode}"
    result_folder.mkdir(exist_ok=True)
    reconstructed: list[str] | list[list[str]]

    match translate_mode:
        case "simple":
            to_translate = deepl_to_translate_path / f"word.txt"
            ct = None
            if not to_translate.exists():
                ct = 0
                with open(to_translate, "w", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
                    idx: int
                    for word in model.vocabulary():
                        if (found := original_dictionary.get_translation_a_to_b(word)) is not None:
                            current = None
                            for value in found:
                                if current is None:
                                    current = value, int(original_dictionary.get_meta_b_of(value).meta_tags[0])
                                else:
                                    other = int(original_dictionary.get_meta_b_of(value).meta_tags[0])
                                    if current[1] < other:
                                        current = value, other
                            f.write(f"{current[0]}\n")
                            ct += 1
                        else:
                            raise AssertionError("Translation defect!")

            if not (result_folder / "words.txt").exists():
                input(r"Please translate the files in {} with deepl to {} (press enter to continue)".format(
                    deepl_to_translate_path.absolute(), result_folder.absolute()))

            with (result_folder / "words.txt").open("r", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
                reconstructed = []
                for line in f:
                    line = line.strip()
                    dat = _process_token_list(processor.process_string(language_hint, line), True)
                    if dat is None:
                        print(f'{line} is empty!')
                        dat = line
                    else:
                        dat = dat[1]
                    reconstructed.append(dat)
                assert ct is None or len(reconstructed) == ct, f"{len(reconstructed)} != {ct}"
        case "complex":
            mapping: list[list[tuple[int, int, float]]] = []
            for k in range(model.k):
                topic: list[tuple[int, str, float]] | None = model.get_topic_as_words(k)
                assert topic is not None, f"Why is {k} failing!?"
                topic: list[tuple[int, tuple[int, str, float]]] = list(enumerate(topic))
                to_translate = deepl_to_translate_path / f"topic_{k}.txt"
                topic: list[tuple[int, tuple[int, str, float]]] = sorted(topic, key=lambda x: x[1][2], reverse=True)
                topic_mapping: list[tuple[int, int, float] | None] = [None] * len(topic)
                with open(to_translate, "w", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
                    idx: int
                    for idx, entry in topic:
                        word_id, word, probability = entry
                        res = idx, word_id, probability
                        if (found := original_dictionary.get_translation_a_to_b(word)) is not None and len(found) > 0:
                            current = None
                            for value in found:
                                if current is None:
                                    current = value, int(original_dictionary.get_meta_b_of(value).meta_tags[0])
                                else:
                                    other = int(original_dictionary.get_meta_b_of(value).meta_tags[0])
                                    if current[1] < other:
                                        current = value, other
                            topic_mapping[idx] = res
                            f.write(f"- {current[0]}.\n")
                        else:
                            print(f"Failed for {entry}!!!!")
                assert all(topic_mapping), f"Something is missing in topic mapping {k}!!"
                mapping.append(topic_mapping)

            deepl_path_structure.write_text(
                jsonpickle.dumps(mapping),
                encoding="UTF-8",
            )

            input(r"Please translate the files in {} with deepl to {} (press enter to continue)".format(
                deepl_to_translate_path.absolute(), result_folder.absolute()))

            reconstructed = []
            for k in range(model.k):
                to_translate = result_folder / f"topic_{k}.txt"
                with open(to_translate, "r", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
                    data = []
                    for line in f:
                        line = line.strip()
                        a = _process_token_list(processor.process_string(language_hint, line), True)
                        if a is None:
                            print(f'{line} is empty!')
                            a = line
                        else:
                            a = a[1]
                        data.append(a)
                    mapp = mapping[k]
                    result: list[str | None] = [None] * len(mapp)
                    for word, map_entry in zip(data, map):
                        result[map_entry[0]] = _process_token_list(processor.process_string(language_hint, word))[1]
                    assert all(result), f"Something is missing for {k}!!!"
                    reconstructed.append(result)
        case invalid:
            raise ValueError(f"Illegal mode: {invalid}")
    new_model = model.translate_by_provided_word_lists(
        "de",
        reconstructed,
    )
    # with open(to_translate, "r", buffering=1024 * 1024 * 200, encoding="UTF-8") as comp:
    #     for a, b, c in itertools.zip_longest(new_model.vocabulary(), comp, reconstructed):
    #         print(f"{a}, {b.strip()}, {c}")

    new_model.save_binary(paper_dir.deepl().model_path)
    b_data = load_test_data(test_data, limit, language_hint)[str(language_hint)]
    new_model.show_top(10)

    b_ratings = create_ratings(new_model, paper_dir.load_original_models()[0].alpha, 0.01, b_data)
    assert len(b_ratings) == len(b_data)
    paper_dir.deepl().rating_path.write_text(jsonpickle.dumps(b_ratings))

    return new_model
