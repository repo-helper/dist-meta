#!/usr/bin/env python3
#
#  record.py
"""
Classes to model parts of ``RECORD`` files.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import csv
import os
import pathlib
import posixpath
import sys
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import TYPE_CHECKING, NamedTuple, Optional, Type, TypeVar

# 3rd party
from domdf_python_tools.stringlist import DelimitedList
from domdf_python_tools.typing import PathLike

if TYPE_CHECKING:
	# stdlib
	from hashlib import _Hash

	# this package
	from dist_meta.distributions import Distribution
else:
	try:
		# 3rd party
		from _hashlib import HASH as _Hash
	except ImportError:  # pragma: no cover
		try:
			# 3rd party
			from _hashlib import Hash as _Hash
		except ImportError:
			pass

__all__ = ("FileHash", "RecordEntry")

_RE = TypeVar("_RE", bound="RecordEntry")
_FH = TypeVar("_FH", bound="FileHash")


class RecordEntry(pathlib.PurePosixPath):
	"""
	Represents a path in a distribution.

	:param path: The path to the file in the distribution, relative to the distribution root
		(i.e. the ``site-packages`` directory).
	:param hash: The hash/checksum of the file.
	:param size: The size of the file.
	:param distro: The distribution the file belongs to.

	.. note::

		Path operations (:meth:`~.pathlib.PurePath.joinpath`, :attr:`~.pathlib.PurePath.parent` etc.)
		will return a standard :class:`pathlib.PurePosixPath` object without the extended attributes of this class.
	"""

	__slots__ = ("hash", "size", "distro")

	#: The name of the file in the distribution.
	name: str

	#: The hash/checksum of the file.
	hash: Optional["FileHash"]  # noqa: A003  # pylint: disable=redefined-builtin

	#: The size of the file.
	size: Optional[int]

	#: The distribution the file belongs to.
	distro: Optional["Distribution"]

	def __init__(
			self,
			path: PathLike,
			hash: Optional["FileHash"] = None,  # noqa: A002  # pylint: disable=redefined-builtin
			size: Optional[int] = None,
			distro: Optional["Distribution"] = None,
			):
		if sys.version_info < (3, 12):  # pragma: no cover (py312+)
			super().__init__()
		else:  # pragma: no cover (<py312)
			super().__init__(self._coerce_path(path))

	def __new__(
			cls: Type[_RE],
			path: PathLike,
			hash: Optional["FileHash"] = None,  # noqa: A002  # pylint: disable=redefined-builtin
			size: Optional[int] = None,
			distro: Optional["Distribution"] = None,
			) -> _RE:
		"""
		Construct a :class:`RecordEntry` from one a string or an existing :class:`pathlib.PurePath` object.
		"""

		self = super().__new__(cls, cls._coerce_path(path))
		self.hash = hash
		self.size = size
		self.distro = distro
		return self

	@classmethod
	def _coerce_path(cls, path: PathLike) -> PathLike:
		"""
		Necessary to fix issue in Python 3.12 where path separators are no longer converted.
		"""

		if os.path.isabs(path):
			raise ValueError("RecordEntry paths cannot be absolute")

		if isinstance(path, pathlib.PurePath):
			if path.is_absolute():
				# Catch absolute paths from other platform
				raise ValueError("RecordEntry paths cannot be absolute")
			path = path.as_posix()
			if posixpath.isabs(path):
				raise ValueError("RecordEntry paths cannot be absolute")

		return path

	def read_text(
			self,
			encoding: Optional[str] = "UTF-8",
			errors: Optional[str] = None,
			) -> str:
		"""
		Open the file in text mode, read it, and close the file.

		:param encoding: The encoding to write to the file in.
		:param errors:

		:return: The content of the file.

		.. attention:: This operation requires a value for :attr:`self.distro <.RecordEntry.distro>`.
		"""

		if self.distro is None:
			raise ValueError("Cannot read files with 'self.distro = None'")

		return (self.distro.path.parent / self).read_text(encoding=encoding, errors=errors)

	def read_bytes(self) -> bytes:
		"""
		Open the file in bytes mode, read it, and close the file.

		:return: The content of the file.

		.. attention:: This operation requires a value for :attr:`self.distro <.RecordEntry.distro>`.
		"""

		if self.distro is None:
			raise ValueError("Cannot read files with 'self.distro = None'")

		return (self.distro.path.parent / self).read_bytes()

	def __repr__(self) -> str:
		"""
		Return a string representation of the :class:`~.RecordEntry`.
		"""

		parts = DelimitedList([f"{os.fspath(self)!r}"])
		if self.hash is not None:
			parts.append(f"hash={self.hash!r}")
		if self.size is not None:
			parts.append(f"size={self.size!r}")
		if self.distro is not None:
			parts.append(f"distro={self.distro!r}")
		return f"{self.__class__.__name__}({parts:, })"

	def as_record_entry(self) -> str:
		"""
		Returns an entry for a ``RECORD`` file, in the form ``<name>,<hash>,<size>``.
		"""

		parts = [self.as_posix()]

		if self.hash is not None:
			parts.append(self.hash.to_string())
		else:
			parts.append('')

		if self.size is not None:
			parts.append(str(self.size))
		else:
			parts.append('')

		return ','.join(parts)

	@classmethod
	def from_record_entry(
			cls: Type[_RE],
			entry: str,
			distro: Optional["Distribution"] = None,
			) -> _RE:
		"""
		Construct a :class:`~.RecordEntry` from a line in a ``RECORD`` file, in the form ``<name>,<hash>,<size>``.

		.. versionadded:: 0.2.0

		:param entry:
		:param distro: The distribution the ``RECORD`` file belongs to. Optional.

		:rtype: :class:`~.RecordEntry`
		"""

		entry = entry.strip()
		lines = entry.splitlines()

		if len(lines) != 1:
			raise ValueError("'entry' must be a single-line entry.")

		entry = lines[0]

		if '"' in entry:
			name, hash_, size_str, *_ = next(csv.reader((entry, )))
		else:
			name, hash_, size_str, *_ = entry.split(',')

		hash_ = hash_.strip()
		size_str = size_str.strip()

		return cls(
				name.strip(),
				hash=FileHash.from_string(hash_) if hash_ else None,
				size=int(size_str) if size_str else None,
				distro=distro,
				)


class FileHash(NamedTuple):
	"""
	Represents a checksum for a file in a ``RECORD`` file, or as the URL fragment in a :pep:`503` repository URL.
	"""

	#: The name of the hash algorithm.
	name: str

	#: The :func:`~.base64.urlsafe_b64encode`'d hexdigest of the hash.
	value: str

	@classmethod
	def from_string(cls: Type[_FH], string: str) -> _FH:
		"""
		Constructs a  :class:`~.FileHash` from a  string in the form ``<name>=<value>``.

		:param string:

		:rtype: :class:`~.FileHash`
		"""

		name, _, value = string.partition('=')
		return cls(name.strip(), value.strip())

	def to_string(self) -> str:
		"""
		Returns the :class:`~.FileHash` as a string, in the form ``<name>=<value>``.
		"""

		return f"{self.name}={self.value}"

	def digest(self) -> bytes:
		"""
		Returns the digest of the hash.

		This is a bytes object which may contain bytes in the whole range from 0 to 255.
		"""

		return urlsafe_b64decode(f"{self.value}==".encode("latin1"))

	def hexdigest(self) -> str:
		"""
		Like :meth:`self.digest() <.FileHash.digest>` except the digest is returned as
		a string object of double length, containing only hexadecimal digits.

		This may be used to exchange the value safely in email or other non-binary environments.
		"""  # noqa: D400

		return ''.join(f"{x:0{2}x}" for x in self.digest())

	@classmethod
	def from_hash(cls: Type[_FH], the_hash: "_Hash") -> _FH:
		"""
		Construct a :class:`~.FileHash` object from a :mod:`hashlib` hash object.

		:param the_hash:
		:type the_hash: :mod:`hashlib.HASH <hashlib>`

		:rtype: :class:`~.FileHash`
		"""

		name = the_hash.name
		value = urlsafe_b64encode(the_hash.digest()).decode("latin1").rstrip('=')
		return cls(name, value)
