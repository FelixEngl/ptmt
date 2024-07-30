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

