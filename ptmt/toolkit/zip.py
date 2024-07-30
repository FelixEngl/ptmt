import abc
import io
import typing
import zipfile
from os import PathLike
from pathlib import Path
from typing import Protocol


class TM_Output(Protocol):
    @abc.abstractmethod
    def open(self, path: str) -> typing.TextIO:
        ...

    def __enter__(self):
        return self


class TM_Output_FileSystem(TM_Output):
    def __init__(self, path: Path | PathLike[str] | str):
        if not isinstance(path, Path):
            path = Path(path)
        self._p = path

    def open(self, path: str) -> typing.TextIO:
        p = self._p / path
        if not p.exists():
            p.parent.mkdir(parents=True)
            p.touch(exist_ok=True)
        return (self._p / path).open('w', encoding='utf-8')


class _TextIO(io.StringIO):
    _z: zipfile.ZipFile

    def __init__(self, z: zipfile.ZipFile, path: str):
        self._z: zipfile.ZipFile = z
        self._p = path
        super().__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._z.writestr(self._p, self.getvalue().encode(encoding='UTF-8'))
        super().__exit__(exc_type, exc_val, exc_tb)


class TM_Output_Zip(TM_Output):
    def __init__(self, path: Path | PathLike[str] | str):
        if not isinstance(path, Path):
            path = Path(path)
        self._z = zipfile.ZipFile(path, mode='w')

    def open(self, path: str) -> typing.TextIO:
        return _TextIO(self._z, path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._z.close()


class TM_Input(Protocol):
    @abc.abstractmethod
    def open(self, path: str) -> typing.TextIO:
        ...

    def __enter__(self):
        return self

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        ...


class TM_Input_FileSystem(TM_Input):
    def __init__(self, path: Path | PathLike[str] | str):
        if not isinstance(path, Path):
            path = Path(path)
        self._p = path

    def open(self, path: str) -> typing.TextIO:
        return (self._p / path).open('r', encoding='utf-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TM_Input_Zip(TM_Input):
    def __init__(self, path: Path | PathLike[str] | str):
        if not isinstance(path, Path):
            path = Path(path)
        self._p = zipfile.ZipFile(path, mode='r')

    def open(self, path: str) -> typing.TextIO:
        return io.TextIOWrapper(self._p.open(path), encoding='UTF-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._p.close()