import itertools
from typing import Iterator, Optional

from ptmt.dictionary_readers.v1.entries import DictionaryEntryComplete
from ptmt.dictionary_readers.v1.readers.linetree import LineTree, LineTreeNode
from ptmt.dictionary_readers.v1.readers.transformer import ColumnType, Separator, SpecialWords, SpecialCharacter, AdditionalInfo, \
    BaseTokenClass, ColumnContentType, BaseInfoTokenClass
from ptmt.dictionary_readers.v1.readers.protocols import ConverterCallable, ToIgnoreFunction


def _default_to_ignore(_):
    return False


def convert_to_all_recombinations(separated_column_content: ColumnContentType,
                                  to_ignore: Optional[ToIgnoreFunction] = None) -> LineTree:
    result_preprocessed = LineTree()
    last: Optional[LineTreeNode] = None
    if to_ignore is None:
        to_ignore = _default_to_ignore

    def set_new_sub_root():
        nonlocal last
        last = result_preprocessed.root.add_child(children=[])

    def add(to_add=None, /, *, children=None):
        nonlocal last
        last = last.add_child(to_add, children=children)

    def branch(new_branch: BaseTokenClass):
        nonlocal last
        last.add_branch(convert_to_all_recombinations(new_branch.value, to_ignore).root)

    for separated_values_to_recombine in separated_column_content:
        set_new_sub_root()
        if any(isinstance(to_recombine, str) for to_recombine in separated_values_to_recombine):
            for i, entry in enumerate(separated_values_to_recombine):
                if issubclass(type(entry), BaseInfoTokenClass):
                    add(entry)
                if to_ignore(entry):
                    continue
                if isinstance(entry, AdditionalInfo):
                    if i == 0:
                        add(children=[])
                    branch(entry)
                elif isinstance(entry, str):
                    add(entry)
                elif isinstance(entry, Separator):
                    last = last.parents[0]
                elif isinstance(entry, SpecialWords):
                    if entry.value == '...':
                        add('...')
                elif isinstance(entry, SpecialCharacter):
                    add(entry.value)

        elif len(separated_values_to_recombine) >= 1:
            add(separated_values_to_recombine[0])
    return result_preprocessed


def extract_dictionary_entries(col_lang_a: ColumnType, col_lang_b: ColumnType, *,
                               converter: Optional[ConverterCallable] = None) -> Iterator[DictionaryEntryComplete]:

    if converter is None:
        converter = convert_to_all_recombinations

    len_col_lang_b = len(col_lang_b)
    len_col_lang_a = len(col_lang_a)

    if len_col_lang_b == len_col_lang_a:
        iterator = zip(col_lang_b, col_lang_a)
    elif len_col_lang_b > len_col_lang_a == 1:
        iterator = itertools.zip_longest(col_lang_b, col_lang_a, fillvalue=col_lang_a[0])
    elif len_col_lang_a > len_col_lang_b == 1:
        iterator = itertools.zip_longest(col_lang_b, col_lang_a, fillvalue=col_lang_b[0])
    else:
        raise ValueError(f'The length of col_german is {len_col_lang_b} and of col_english {len_col_lang_a}.')

    for cont_lang_b, cont_lang_a in iterator:
        cont_lang_b: ColumnContentType
        cont_lang_a: ColumnContentType
        lang_b = list(converter(cont_lang_b).root.get_all_combinations())
        lang_a = list(converter(cont_lang_a).root.get_all_combinations())
        for langB, langA in itertools.product(lang_b, lang_a):
            yield DictionaryEntryComplete(
                ' '.join(str(x) for x in langB if x.is_text),
                ' '.join(str(x) for x in langA if x.is_text),
                langB_meta=tuple(str(x) for x in langB if x.is_meta),
                langA_meta=tuple(str(x) for x in langA if x.is_meta),
                #de_add=' '.join(str(x) for x in langA if x.is_add),
                #en_add=' '.join(str(x)for x in langA if x.is_add),
                langB_original_tokens=langB,
                langA_original_tokens=langA
            )
