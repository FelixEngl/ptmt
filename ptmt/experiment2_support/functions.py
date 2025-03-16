import inspect
import re
from typing import Optional

import numpy
import regex
from ldatranslate.ldatranslate import BoostMethod

from ptmt.create.horizontal import HorizontalBoostFactory, HorizontalKwargs, create_horizontal_factory
from ptmt.create.ngram import NGramBoostKwargs, NGramFactory, create_ngram_language_boost_factory
from ptmt.create.vertical import VerticalBoostFactory, VerticalKwargs, create_vertical_factory
from ptmt.experiment2_configs import *
from ptmt.research.protocols import TranslationConfig
from ptmt.toolkit.combination_creator import yield_all_configs, estimate_complete_count, \
    Single


def modifier_factory(
    *,
    vertical: Optional[VerticalBoostFactory] = None,
    horizontal: Optional[HorizontalBoostFactory] = None,
    ngram: Optional[NGramFactory] = None,
) -> typing.Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig]:
    def config_modifier(config: TranslationConfig, _: PyTopicModel, dictionary: PyDictionary) -> PyTranslationConfig:

        counts: dict[Domain | Register | int, int] = dictionary.dictionary_meta_counts().a().as_dict()

        target_value = numpy.percentile(
            list(counts.values()),
            10
        )

        targets: list[Domain | Register | int] = []
        for k, v in counts.items():
            if v >= target_value:
                targets.append(k)

        a = None
        if vertical is not None:
            a = vertical(targets)
        b = None
        if horizontal is not None:
            b = horizontal(targets)

        c = None
        if ngram is not None:
            c = ngram()

        return PyTranslationConfig(
            None,
            None,
            config.keep,
            None,
            a,
            b,
            c
        )
    return config_modifier


def _single_word(k: str, v: Any) -> str:
    if isinstance(v, float):
        u = f'{v:.4f}'.replace('.', '-')
    # elif v is None:
    #     u = '#'
    # elif isinstance(v, bool):
    #     if v:
    #         u = '+'
    #     else:
    #         u = '?'
    elif (isinstance(v, MeanMethod)
          or isinstance(v, BoostMethod)
          or isinstance(v, ScoreModifierCalculator)
          or isinstance(v, BoostNorm)
          or isinstance(v, FDivergence)
          or isinstance(v, NormalizeMode)
    ):
        u = ''.join(filter(lambda c: c.isupper(), str(v)))
    elif isinstance(v, dict):
        return _compact(f"bo{k[-1]}", v)
    else:
        u = str(v)[0]
    return f'{k[0]}{u}'

def _compact(start: str, info: dict[str, Any] | None) -> str:
    s1 = start
    if info is not None and len(info) > 0:
        for k, v in info.items():
            s1 += _single_word(k, v)
    else:
        s1 += '#'
    return s1


# _re = re.compile(r'(?:bo([a-z]))?([a-z]+)(?:([A-Z]+)|(\d+)-(\d+)|([+?#]))')
#
# def _uncompact(target: type, s: str):
#     if s == '#':
#         return None
#     print(f'FOR {target}:')
#     value = inspect.get_annotations(target)
#     print(f"{value}")
#     for match in _re.finditer(s):
#         if match[0] is not None:
#             print("BuildSub")
#             continue
#         if match
#
#         print(match.groups())
#
#
#
# def read_name(full_name: str) -> (str, Optional[VerticalKwargs], Optional[HorizontalKwargs], Optional[NGramBoostKwargs]):
#     splitted = tuple(full_name.split('_'))
#     for v in splitted[1:]:
#         match v[0]:
#             case 'V':
#                 _uncompact(VerticalKwargs, v[1:])
#             case 'H':
#                 _uncompact(HorizontalKwargs, v[1:])
#             case 'N':
#                 _uncompact(NGramBoostKwargs, v[1:])

# if __name__ == '__main__':
#     n = 'v3_Va1-0000dJf1-0000nNoTsWS_Ha1-0000bPdTf1-5000h0-5000lNmMMMnMoTsN_NboabSf1-0000fNiInNoTbobbMf1-0000fNiInNoT'
#     read_name(n)

def create_name(
        vertical: Optional[VerticalKwargs] = None,
        horizontal: Optional[HorizontalKwargs] = None,
        ngram: Optional[NGramBoostKwargs] = None,
) -> tuple[str, str, str]:
    v = _compact('V', vertical)
    h = _compact('H', horizontal)
    n = _compact('N', ngram)
    return v, h, n


def _needs_alpha(div: FDivergence) -> bool:
    if FDivergence.Renyi == div:
        return True
    return False


def calculate_with_alpha_specific(**base_cfg) -> int:
    if len(base_cfg) == 0:
        return 0
    divergences = list(yield_all_configs(divergence=base_cfg['divergence']))
    alphas = list(yield_all_configs(alpha=base_cfg['alpha']))
    base_cfg_cleaned = dict(base_cfg)
    del base_cfg_cleaned['divergence']
    del base_cfg_cleaned['alpha']

    ct = 0
    for div in divergences:
        cfg = dict(base_cfg_cleaned)
        cfg['divergence'] = Single(div)
        if _needs_alpha(div['divergence']):
            cfg['alpha'] = alphas
        else:
            cfg['alpha'] = None
        ct += estimate_complete_count(**cfg)
    return ct

def determine_all_combinations() -> int:
    n_gram = estimate_complete_count(**n_config_base)
    n_grams = n_gram*n_gram
    if n_grams == 0:
        n_grams = 1
    h_configs = calculate_with_alpha_specific(
        **h_configs_base
    )
    if h_configs == 0:
        h_configs = 1
    v_configs = calculate_with_alpha_specific(
        **v_configs_base
    )
    if v_configs == 0:
        v_configs = 1
    return h_configs * v_configs * n_grams


def create_all_configs() -> typing.Iterator[tuple[HorizontalKwargs, VerticalKwargs, NGramBoostKwargs]]:

    def fm(v):
        if v is None:
            return True
        if 'divergence' not in v:
            return True
        if not _needs_alpha(v['divergence']):
            return True
        return _needs_alpha(v['divergence']) and v['alpha'] is not None

    h_configs: typing.Iterator[HorizontalKwargs] = filter(
        fm,
        yield_all_configs(**h_configs_base),
    )

    v_configs: typing.Iterator[VerticalKwargs] = filter(
        fm,
        yield_all_configs(**v_configs_base),
    )


    def n_configs_creator():
        for a, b in itertools.product(
            yield_all_configs(**n_config_base),
            yield_all_configs(**n_config_base)
        ):
            if a is None and b is None:
                yield None
            else:
                yield {
                    'boost_lang_a': a,
                    'boost_lang_b': b,
                }

    n_configs = n_configs_creator()

    return itertools.product(
        h_configs,
        v_configs,
        n_configs,
    )