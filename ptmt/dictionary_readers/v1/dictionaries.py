import abc
import functools
import importlib
import inspect
import re
import sys
import typing
from collections import defaultdict
from os import PathLike
from pathlib import Path

import langcodes

from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.dictionary_readers.v1.entries import DictionaryEntry


_Language = LanguagePair | tuple[str, str] | tuple[langcodes.Language, langcodes.Language]


class LanguagesNotSupportedError(LookupError):
    def __init__(self, target: typing.Callable[..., typing.Any], languages: LanguagePair, cause: TypeError | None = None):
        self.languages: LanguagePair = languages
        self.target: typing.Callable[..., typing.Any] = target
        self.cause = cause

    def __str__(self):
        if self.cause is not None:
            return f"No additional parameters for {self.languages} are registered for {self.target.__name__}() but {self.cause}!"
        return f"No additional parameters for {self.languages} are registered for {self.target}!"


class DictionaryCall(typing.TypedDict):
    suppress_error_print: typing.NotRequired[bool]


class DictionaryReaderLike(typing.Protocol):
    """
    Anything that can be similar to a dictionary reader.
    """
    def __call__(self, languages: _Language, data_path: Path | str | PathLike[str], *args,
                 **kwargs: typing.Unpack[DictionaryCall]) -> typing.Iterator[DictionaryEntry]: ...


@typing.runtime_checkable
class DictionaryReaderBase(DictionaryReaderLike, typing.Protocol):
    """
    Baseclass of DictionaryReader to allow circular type dependency resolution
    """

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def __str__(self): ...


@typing.runtime_checkable
class DictionaryReader(DictionaryReaderBase, typing.Protocol):

    @abc.abstractmethod
    def can_skip_by(self, names_to_skip: set[str | DictionaryReaderBase]) -> bool:...

    @abc.abstractmethod
    def read_dictionary(self, languages: _Language, data_path: Path | str | PathLike[str], *args,
                        **kwargs: typing.Unpack[DictionaryCall]) -> typing.Iterator[DictionaryEntry]: ...

    @abc.abstractmethod
    def __call__(self, languages: _Language, data_path: Path | str | PathLike[str], *args,
                 **kwargs: typing.Unpack[DictionaryCall]) -> typing.Iterator[DictionaryEntry]: ...


_registered_dictionary_builder: dict[str, list[DictionaryReader]] = defaultdict(list)

_module = "dictionary_readers.v1.dictionary_reader_declarations"
def all_registered_dictionaries() -> list[DictionaryReader]:
    # noinspection PyUnresolvedReferences
    if _module not in sys.modules:
        importlib.import_module(_module)
    return [known for all_known in _registered_dictionary_builder.values() for known in all_known]


def _filter_kwargs_for(thing_with_kwargs: typing.Callable[..., typing.Any], dict_to_filter: dict[str, typing.Any]):

    spec = inspect.getfullargspec(thing_with_kwargs)
    if spec.varkw is not None:
        return dict_to_filter

    sig = inspect.signature(thing_with_kwargs)
    filter_keys = [param.name for param in sig.parameters.values() if param.kind == param.POSITIONAL_OR_KEYWORD]
    filtered_dict = {filter_key:dict_to_filter[filter_key] for filter_key in filter_keys if filter_key in dict_to_filter}
    return filtered_dict


class _DirectionBasedDictionaryReader(DictionaryReader):

    _func: DictionaryReaderLike
    _additional_params: dict[LanguagePair, list[tuple[tuple, dict[str, typing.Any]] | typing.Callable[[], tuple[tuple, dict[str, typing.Any]]]]]
    _default_params: tuple[tuple, dict[str, typing.Any]] | typing.Callable[[], tuple[tuple, dict[str, typing.Any]]] | None
    _name: str
    _requires_reader_args: bool

    def __new__(cls, func: DictionaryReaderLike, name: str | None = None, force_reader_args: bool | None = False):
        created = super().__new__(_DirectionBasedDictionaryReader)
        created.__init__(func, name, force_reader_args)
        _registered_dictionary_builder[created.name].append(created)
        return created

    # noinspection PyProtocol
    def __init__(self, func: DictionaryReaderLike, name: str | None = None, force_reader_args: bool | None = False):
        if isinstance(func, DictionaryReader):
            raise ValueError("Can not nest this wrapper!")
        else:
            self._additional_params = dict()
            self._func = func
            self._default_params = None
            functools.update_wrapper(self, func)
            self._name = name if name is not None else self._func.__name__
            first = inspect.getfullargspec(self._func).args[0]
            if force_reader_args is None:
                self._requires_reader_args = re.fullmatch("_+", first) is not None
            else:
                self._requires_reader_args = force_reader_args


    @property
    def name(self) -> str:
        return self._name

    def force_requires_registration_of_additional_params(self, value: bool):
        self._requires_reader_args = value

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, DictionaryReaderBase):
            return self._name == other.name
        if isinstance(other, str):
            return self._name == other
        return False

    def can_skip_by(self, names_to_skip: set[str | DictionaryReaderBase]) -> bool:
        if self in names_to_skip:
            return True
        names_to_skip = set(map(str, names_to_skip))
        return self._name in names_to_skip

    def register_default(self, *args, **kwargs):
        assert self._default_params is None, "Default already set"
        self._default_params = (args, kwargs)

    def register(self, languages: LanguagePair, __allow_reverse: bool, *args, **kwargs):
        val = (args, kwargs)
        current = self._additional_params.get(languages, None)
        if current is None:
            current = list()
            self._additional_params[languages] = current
        current.append(val)
        if __allow_reverse:
            self.register(
                LanguagePair(languages.langB, languages.langA),
                False,
                False,
                *args,
                **kwargs
            )


    def read_dictionary(self, languages: _Language, data_path: Path | str | PathLike[str],
                        *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
        if isinstance(languages, tuple):
            languages = LanguagePair.create(languages)
        found = self._additional_params.get(languages, None)
        if self._requires_reader_args and found is None:
            raise LanguagesNotSupportedError(self._func, languages)

        if found is None and self._default_params is not None:
            found = [self._default_params]

        try:
            if found is not None:
                found = [value if isinstance(value, tuple) else value() for value in found]
                for value in found:
                    if not isinstance(value, tuple):
                        assert callable(value), "Only tuples and callables allowed!"
                        value = value()
                    if len(args) != 0:
                        target_args = args
                    else:
                        target_args = args if value[0] is None else value[0]
                    target_kwargs = dict(kwargs)
                    target_kwargs.update(value[1])
                    target_kwargs = _filter_kwargs_for(self._func, target_kwargs)
                    yield from self._func(languages, data_path, *target_args, **target_kwargs)
            else:
                kwargs = _filter_kwargs_for(self._func, kwargs)
                yield from self._func(languages, data_path, *args, **kwargs)
        except TypeError as e:
            raise LanguagesNotSupportedError(self._func, languages, e)

    def __call__(self, languages: _Language, data_path: Path | str | PathLike[str], *args,
                 **kwargs: typing.Unpack[DictionaryCall]) -> typing.Iterator[DictionaryEntry]:
        return self.read_dictionary(languages, data_path, *args, **kwargs)

    def __str__(self):
        return self._name


_WrapperReturnType = DictionaryReader | typing.Callable[[DictionaryReaderLike], DictionaryReader]


def as_dictionary_reader(name: DictionaryReaderLike | _DirectionBasedDictionaryReader | str,
                         /,
                         force_dictionary_reader_args: bool | None = None) -> _WrapperReturnType:
    """
    The first 2 args of a method converted to a DictionaryReader instance have to be 'languages: LanguagePair' and
    'data_path: Path | PathLike[str] | str' followed by any named parameters needed.

    If parameter 1 matches the regex _+ (e.g. _, __, ___), you HAVE to register  additional args with register_dictionary_reader_args for every supported language.
    Otherwise the method call fails.

    If you want to call the method without dictionary_reader_args but you ignore the first argument, you have to set
    force_dictionary_reader_args=False.

    The last 2 parameters CAN be *args **kwargs if there are some relayed parameters.
    """

    if isinstance(name, str):
        def wrap(f: DictionaryReaderLike | _DirectionBasedDictionaryReader) -> DictionaryReader:
            if not isinstance(f, _DirectionBasedDictionaryReader):
                f = _DirectionBasedDictionaryReader(f, name, force_reader_args=force_dictionary_reader_args)
            return f
        return wrap
    elif isinstance(name, _DirectionBasedDictionaryReader):
        return name
    else:
        return _DirectionBasedDictionaryReader(name, force_reader_args=force_dictionary_reader_args)


def register_default_dictionary_reader_args(*args, **kwargs) \
        -> _WrapperReturnType:
    """
    Allows to specify the default values for all dictionary reader args if they are not provided by the caller.
    """
    def wrap(f: DictionaryReaderLike | _DirectionBasedDictionaryReader) -> _DirectionBasedDictionaryReader:
        if not isinstance(f, _DirectionBasedDictionaryReader):
            f = _DirectionBasedDictionaryReader(f)
        f.register_default(*args, **kwargs)
        return f
    return wrap


def require_dictionary_reader_args(target: DictionaryReaderLike | _DirectionBasedDictionaryReader) -> _WrapperReturnType:
    """
    Forces the usage of register_dictionary_reader_args
    """
    if not isinstance(target, _DirectionBasedDictionaryReader):
        target = _DirectionBasedDictionaryReader(target)
    target.force_requires_registration_of_additional_params(True)
    return target


def ignore_missing_dictionary_reader_args(target: DictionaryReaderLike | _DirectionBasedDictionaryReader) -> _WrapperReturnType:
    """
    Forces the usage of register_dictionary_reader_args
    """
    if not isinstance(target, _DirectionBasedDictionaryReader):
        target = _DirectionBasedDictionaryReader(target)
    target.force_requires_registration_of_additional_params(False)
    return target


def register_dictionary_reader_args(
        languages: DictionaryReaderLike | _DirectionBasedDictionaryReader | _Language | str | langcodes.Language,
        *args,
        __allow_reverse: bool = False,
        **kwargs,
) -> _WrapperReturnType:
    """
    Allows to specify the translation direction supported by the dictionary reader and additional default args kwargs
    if they are not provided by the caller.

    The languages argument can be set as LanguagePair, tuple[str, str] or two str args.

    Set __allow_reverse to True to allow the reverse the languages and keeping all other args the same.
    """
    if isinstance(languages, str) or isinstance(languages, langcodes.Language):
        assert isinstance(args[0], str)
        languages = LanguagePair.create(languages, args[0])
        args = args[1:]
    if isinstance(languages, tuple):
        languages = LanguagePair.create(languages)
    if isinstance(languages, LanguagePair):
        def wrapper(f: DictionaryReaderLike | _DirectionBasedDictionaryReader) -> _DirectionBasedDictionaryReader:
            if not isinstance(f, _DirectionBasedDictionaryReader):
                f = _DirectionBasedDictionaryReader(f)
            if isinstance(languages, tuple) and len(languages) == 0:
                f.register_default(*args, **kwargs)
            else:
                f.register(languages, __allow_reverse, *args, **kwargs)
            return f
        return wrapper
    if not isinstance(languages, _DirectionBasedDictionaryReader):
        languages = _DirectionBasedDictionaryReader(languages)
    if len(args) != 0 or len(kwargs) != 0:
        languages.register(args[0], __allow_reverse, *args[1:], **kwargs)
    return languages
