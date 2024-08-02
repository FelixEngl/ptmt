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

import glob as gglob
import inspect
import re
from functools import wraps
from os import PathLike
from pathlib import Path
from typing import Union, Optional, Set

_precompiled_path_pattern = re.compile('[/:"*?<>|\\\\]+')


def to_windows_path_str(s: str, replace_char='-') -> str:
    return _precompiled_path_pattern.sub(replace_char, s)


PathObj = Union[str, Path, PathLike[str]]

_allowed_annots = [
    Union[str, Path],
    Optional[Union[str, Path]],
    Union[str, Path, None],
    PathObj,
    Optional[PathObj],
    Path
]

_allowed_annots_as_str = [
    'Union[str, Path]',
    'Optional[Union[str, Path]]',
    'Union[str, Path, None]',
    'PathObj',
    'Optional[PathObj]',
    'Path'
]


def str_to_path(func):
    """
    Wrapper function for a method to convert string typed args to paths.
    """

    sig: inspect.Signature = inspect.signature(func)

    annots = [k for k, v in sig.parameters.items() if
              (v.annotation in _allowed_annots or
               v.annotation in _allowed_annots_as_str) and not (v.annotation == str or v.annotation == 'str')]

    @wraps(func)
    def wrapper(*args, **kwargs):
        calargs = inspect.getcallargs(func, *args, **kwargs)
        for k in annots:
            if isinstance(calargs[k], str):
                calargs[k] = Path(calargs[k])
        return func(**calargs)

    return wrapper


@str_to_path
def find_and_condense_all_paths_for_glob(path: Union[str, Path],
                                         glob: str,
                                         trim_file_name: bool = True) -> Set[str]:
    retval = set()
    for ob in gglob.iglob(str((path / glob).absolute()), recursive=True):
        if trim_file_name:
            retval.add(str(Path(ob).parent.absolute()))
        else:
            retval.add(ob)

    return retval


@str_to_path
def to_console_clickable(path: Union[str, Path]) -> str:
    return 'file:///' + str(path.absolute()).replace('\\', '/')
