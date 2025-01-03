import typing

from ldatranslate import Idf, BoostMethod, BoostNorm, LanguageHint
from ldatranslate import PyNGramBoostConfig, PyNGramLanguageBoostConfig


class NGramFactory(typing.Protocol):
    def __call__(self) -> PyNGramBoostConfig | None:
        ...

class NGramLanguageBoostKwargs(typing.TypedDict):
    idf: Idf
    boosting: typing.NotRequired[BoostMethod]
    norm: typing.NotRequired[BoostNorm]
    factor: typing.NotRequired[float]
    fallback_language: typing.NotRequired[LanguageHint | str]
    only_positive_boost: typing.NotRequired[bool]

class NGramBoostKwargs(typing.TypedDict):
    boost_lang_a: typing.NotRequired[NGramLanguageBoostKwargs]
    boost_lang_b: typing.NotRequired[NGramLanguageBoostKwargs]


def create_ngram_language_boost_factory(
        *,
        boost_lang_a: NGramLanguageBoostKwargs | None = None,
        boost_lang_b: NGramLanguageBoostKwargs | None = None,
) -> NGramFactory:
    if boost_lang_a is None and boost_lang_b is None:
        return lambda: None
    def factory() -> PyNGramBoostConfig:
        if boost_lang_a is not None:
            a = PyNGramLanguageBoostConfig(
                **boost_lang_a
            )
        else:
            a = None

        if boost_lang_b is not None:
            b = PyNGramLanguageBoostConfig(
                **boost_lang_b
            )
        else:
            b = None

        return PyNGramBoostConfig(a, b)
    return factory