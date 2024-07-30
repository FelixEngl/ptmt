import warnings

from ptmt.dictionary_readers.v1.dictionaries import DictionaryReader, DictionaryReaderLike, \
    all_registered_dictionaries, LanguagesNotSupportedError, DictionaryCall
from ptmt.dictionary_readers.v1.dictionary_reader_declarations import *
from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.dictionary_readers.v1.entries import EDictionaryEntrySizeConversion, DictionaryEntry, to_slim, to_complete, to_reduced
from ptmt.toolkit.paths import PathObj


def load_from_multiple_sources(
        path: PathObj ,
        languages: LanguagePair | tuple[str, str],
        *sources: DictionaryReader | DictionaryReaderLike,
        size_conversion: EDictionaryEntrySizeConversion = EDictionaryEntrySizeConversion.NONE,
        skip: set[str | DictionaryReader] | None = None,
        **kwargs: typing.Unpack[DictionaryCall]
) -> typing.Iterator[DictionaryEntry]:
    """
    Load all dict entries from multiple sources
    :param path to the root folder containing dictionaries.
    :param languages: LanguagePair containing the languages needed in the dictionary.
    :param sources: The sources used for loading the entries. If no sources are provided if falls back to the default all_registered_dictionaries
    :param size_conversion: Reduces the memory footprint of the DictionaryEntries produced by this function by calling
                            the given EDictionaryEntrySizeConversion.
    :skip: DictionaryReaders that have to be skipped.
    :return: Returns an iterator with all possible dictionary entries
    """

    kwargs.setdefault('suppress_error_print', False)

    if len(sources) == 0:
        sources = tuple(all_registered_dictionaries())

    languages = languages if isinstance(languages, LanguagePair) else LanguagePair(*languages)

    if not isinstance(path, Path):
        path = Path(path)

    ct = 0

    def iterate(it: DictionaryReader) -> typing.Iterator[DictionaryEntry]:
        nonlocal ct, skip, path
        if skip is not None and it.can_skip_by(skip):
            print(f"Skip:    <{it.name}>")
            return
        ct_local = 0
        name = it.name
        print(f'Start:    <{name}>')
        try:
            for entry in it(languages, path, **kwargs):
                ct_local += 1
                entry.origin = name
                if size_conversion == EDictionaryEntrySizeConversion.NONE.name:
                    entry = to_slim(entry)
                elif size_conversion.name == EDictionaryEntrySizeConversion.REDUCED.name:
                    entry = to_reduced(entry)
                elif size_conversion.name == EDictionaryEntrySizeConversion.COMPLETE.name:
                    entry = to_complete(entry)
                yield entry
        except LanguagesNotSupportedError as e:
            warnings.warn(str(e))
        except FileNotFoundError as e:
            warnings.warn(str(e))
        ct += ct_local
        print(f'Loaded:   <{ct_local}> for <{name}>!')
        print(f'Returned: <{ct}> entries')

    sources = (value if isinstance(value, DictionaryReader) else as_dictionary_reader(value) for value in sources)

    for source in sources:
        # TODO: processing!
        yield from iterate(source)
