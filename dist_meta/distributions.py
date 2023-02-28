#!/usr/bin/env python3
#
#  distributions.py
"""
Iterate over installed distributions.

Third-party distributions are installed into Python's ``site-packages`` directory with tools such as pip_.
Distributions must have a ``*.dist-info`` directory (as defined by :pep:`566`) to be discoverable.

.. _pip: https://pypi.org/project/pip/
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
#  Parts of iter_distributions based on https://github.com/takluyver/entrypoints
#  Copyright (c) 2015 Thomas Kluyver and contributors
#  MIT Licensed
#

# stdlib
import abc
import collections
import functools
import posixpath
import sys
from contextlib import suppress
from csv import reader as csv_reader
from operator import itemgetter
from typing import (
		TYPE_CHECKING,
		Any,
		Callable,
		Dict,
		Iterable,
		Iterator,
		List,
		Mapping,
		Optional,
		Tuple,
		Type,
		TypeVar
		)

# 3rd party
import handy_archives
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from domdf_python_tools.utils import divide
from packaging.version import Version

# this package
from dist_meta import metadata, wheel
from dist_meta._utils import _canonicalize, _iter_dist_infos, _parse_version, _parse_wheel_filename
from dist_meta.metadata_mapping import MetadataMapping
from dist_meta.record import FileHash, RecordEntry

_tuplegetter = lambda index, doc: property(itemgetter(index), doc=doc)

if not TYPE_CHECKING:
	with suppress(ImportError):
		# 3rd party
		from _collections import _tuplegetter

__all__ = (
		"get_distribution",
		"iter_distributions",
		"packages_distributions",
		"DistributionType",
		"Distribution",
		"WheelDistribution",
		"DistributionNotFoundError",
		"_DT",
		)

_DT = TypeVar("_DT", bound="DistributionType")
_D = TypeVar("_D", bound="Distribution")
_WD = TypeVar("_WD", bound="WheelDistribution")


class DistributionType(abc.ABC):
	"""
	Abstract base class for :class:`~.Distribution`-like objects.

	.. versionchanged:: 0.3.0

		Previously was a :py:obj:`~.typing.Union` representing :class:`~.Distribution` and :class:`~.WheelDistribution`.
		Now a common base class for those two classes, and custom classes providing the same API

	This class implements most of the :func:`collections.namedtuple` API.
	Subclasses must implement ``_fields`` (as a tuple of field names)
	and the :class:`tuple` interface (specifically ``__iter__`` and ``__getitem__``).
	"""

	#: The name of the distribution. No normalization is performed.
	name: str

	#: The version number of the distribution.
	version: Version

	#: A tuple of field names for the "namedtuple".
	_fields: Tuple[str, ...]  # actually a ClassVar, but need to support older Pythons

	#: A mapping of field names to default values.
	_field_defaults: Dict[str, Any]

	# These must be implemented by subclasses
	__iter__: Callable
	__getitem__: Callable

	def __init_subclass__(cls: Type["DistributionType"], **kwargs):

		if not getattr(cls, "_fields", ()):
			raise ValueError("'_fields' cannot be empty.")

		ns = cls.__dict__
		field_defaults = getattr(cls, "_field_defaults", {})

		for index, name in enumerate(cls._fields):  # pylint: disable=use-dict-comprehension
			if name in ns:
				field_defaults[name] = ns[name]

		if cls._fields[0] != "name":
			raise ValueError("The first item in '_fields' must be 'name'")
		elif cls._fields[1] != "version":
			raise ValueError("The second item in '_fields' must be 'version'")

		for index, name in enumerate(cls._fields):
			# pylint: disable=dotted-import-in-loop,loop-global-usage
			doc = sys.intern(f'Alias for field number {index}')
			setattr(cls, name, _tuplegetter(index, doc))
			# pylint: enable=dotted-import-in-loop,loop-global-usage

		cls._field_defaults = field_defaults

	@abc.abstractmethod
	def read_file(self, filename: str) -> str:
		"""
		Read a file from the ``*.dist-info`` directory and return its content.

		:param filename:
		"""

		raise NotImplementedError

	@abc.abstractmethod
	def has_file(self, filename: str) -> bool:
		"""
		Returns whether the ``*.dist-info`` directory contains a file named ``filename``.

		:param filename:
		"""

		raise NotImplementedError

	def _asdict(self) -> Dict[str, Any]:
		"""
		Return a new dict which maps field names to their values.
		"""

		return dict(zip(self._fields, self))

	def __getnewargs__(self) -> Tuple:
		"""
		Return self as a plain tuple. Used by copy and pickle.
		"""

		return tuple(self)

	def _replace(self: _DT, **kwargs) -> _DT:
		"""
		Make a new :class:`~.DistributionType` object, of the same type as this one,
		replacing the specified fields with new values.

		:param iterable:
		"""  # noqa: D400

		result = self._make(map(kwargs.pop, self._fields, self))
		if kwargs:
			raise ValueError(f"Got unexpected field names: {list(kwargs)!r}")
		return result

	@classmethod
	def _make(cls: Type[_DT], iterable) -> _DT:  # noqa: MAN001
		"""
		Make a new :class:`~.DistributionType` object, of the same type as this one, from a sequence or iterable.

		:param iterable:
		"""

		return cls(*iterable)

	def get_entry_points(self) -> Dict[str, Dict[str, str]]:  # -> EntryPointMap
		"""
		Returns a mapping of entry point groups to entry points.

		Entry points in the group are contained in a dictionary mapping entry point names to objects.

		:class:`dist_meta.entry_points.EntryPoint` objects can be constructed as follows:

		.. code-block:: python

			for name, epstr in distro.get_entry_points().get("console_scripts", {}).items():
				EntryPoint(name, epstr)
		"""

		# this package
		from dist_meta import entry_points

		if self.has_file("entry_points.txt"):
			return entry_points.loads(self.read_file("entry_points.txt"))

		return {}

	def get_metadata(self) -> MetadataMapping:
		"""
		Returns the content of the ``*.dist-info/METADATA`` file.
		"""

		return metadata.loads(self.read_file("METADATA"))

	def get_wheel(self) -> Optional[MetadataMapping]:
		"""
		Returns the content of the ``*.dist-info/WHEEL`` file, or :py:obj:`None` if the file does not exist.

		The file will only be present if the distribution was installed from a :pep:`wheel <427>`.
		"""  # noqa: RST399

		if self.has_file("WHEEL"):
			return wheel.loads(self.read_file("WHEEL"))

		return None

	def get_record(self) -> Optional[List[RecordEntry]]:
		"""
		Returns the parsed content of the ``*.dist-info/RECORD`` file, or :py:obj:`None` if the file does not exist.

		:returns: A :class:`dist_meta.record.RecordEntry` object for each line in the record
			(i.e. each file in the distribution).
			This includes files in the ``*.dist-info`` directory.
		"""

		if self.has_file("RECORD"):
			content = self.read_file("RECORD").splitlines()
			output = []

			for line in csv_reader(content):
				name, hash_, size_str, *_ = line
				entry = RecordEntry(
						name.strip(),
						hash=FileHash.from_string(hash_) if hash_ else None,
						size=int(size_str) if size_str else None,
						)
				output.append(entry)

			return output
		else:
			return None

	def __repr__(self) -> str:
		"""
		Returns a string representation of the :class:`~.DistributionType`.
		"""

		return f"<{self.__class__.__name__}({self.name!r}, {self.version!r})>"


class Distribution(DistributionType, Tuple[str, Version, PathPlus]):
	"""
	Represents an installed Python distribution.

	:param name: The name of the distribution.
	"""

	#: The name of the distribution. No normalization is performed.
	name: str

	#: The version number of the distribution.
	version: Version

	#: The path to the ``*.dist-info`` directory in the file system.
	path: PathPlus

	__slots__ = ()
	_fields = ("name", "version", "path")

	def __new__(
			cls: Type[_D],
			name: str,
			version: Version,
			path: PathPlus,
			) -> _D:
		"""
		Construct a new :class:`~.Distribution` object.

		:rtype: :class:`~.Distribution`
		"""

		# If this is super().__new__ it breaks on PyPy
		return tuple.__new__(cls, (name, version, path))

	@classmethod
	def from_path(cls: Type[_D], path: PathLike) -> _D:
		"""
		Construct a :class:`~.Distribution` from a filesystem path to the ``*.dist-info`` directory.

		:param path:

		:rtype: :class:`~.Distribution`
		"""

		path = PathPlus(path)
		if path.name[0] == '~':
			raise ValueError(
					"Directory path starts with a tilde (~). "
					"This may be a temporary directory created by pip.",
					)
		distro_name_version = path.stem

		# Check works around https://foss.heptapod.net/pypy/pypy/-/issues/3579

		if sys.implementation.name == "pypy":  # pragma: no cover (!PyPy)
			if distro_name_version == "hpy":
				name, version = "hpy", "0.0.0"
			elif distro_name_version == "cffi":
				name, version = "cffi", "0.0.0"
			else:
				name, version = divide(distro_name_version, '-')
		else:
			name, version = divide(distro_name_version, '-')

		return cls(name, _parse_version(version), path)

	def read_file(self, filename: str) -> str:
		"""
		Read a file from the ``*.dist-info`` directory and return its content.

		:param filename:
		"""

		return (self.path / filename).read_text()

	def has_file(self, filename: str) -> bool:
		"""
		Returns whether the ``*.dist-info`` directory contains a file named ``filename``.

		:param filename:
		"""

		return (self.path / filename).is_file()

	def get_record(self) -> Optional[List[RecordEntry]]:
		"""
		Returns the parsed content of the ``*.dist-info/RECORD`` file, or :py:obj:`None` if the file does not exist.

		:returns: A :class:`dist_meta.record.RecordEntry` object for each line in the record
			(i.e. each file in the distribution).
			This includes files in the ``*.dist-info`` directory.
		"""

		if self.has_file("RECORD"):
			content = self.read_file("RECORD").splitlines()
			output = []

			for line in csv_reader(content):
				name, hash_, size_str, *_ = line
				entry = RecordEntry(
						name.strip(),
						hash=FileHash.from_string(hash_) if hash_ else None,
						size=int(size_str) if size_str else None,
						distro=self,
						)
				output.append(entry)

			return output
		else:
			return None


class WheelDistribution(DistributionType, Tuple[str, Version, PathPlus, handy_archives.ZipFile]):
	"""
	Represents a Python distribution in :pep:`wheel <427>` form.

	:param name: The name of the distribution.


	A :class:`~.WheelDistribution` can be used as a contextmanager,
	which will close the underlying :class:`zipfile.ZipFile` when exiting
	the :keyword:`with` block.
	"""  # noqa: RST399

	#: The name of the distribution. No normalization is performed.
	name: str

	#: The version number of the distribution.
	version: Version

	#: The path to the ``.whl`` file.
	path: PathPlus

	#: The opened zip file.
	wheel_zip: handy_archives.ZipFile

	__slots__ = ()
	_fields = ("name", "version", "path", "wheel_zip")

	def __new__(
			cls: Type[_WD],
			name: str,
			version: Version,
			path: PathPlus,
			wheel_zip: handy_archives.ZipFile,
			) -> _WD:
		"""
		Construct a new :class:`~.WheelDistribution` object.

		:rtype: :class:`~.WheelDistribution`
		"""

		# If this is super().__new__ it breaks on PyPy
		return tuple.__new__(cls, (name, version, path, wheel_zip))

	@classmethod
	def from_path(cls: Type[_WD], path: PathLike, **kwargs) -> _WD:
		r"""
		Construct a :class:`~.WheelDistribution` from a filesystem path to the ``.whl`` file.

		:param path:
		:param \*\*kwargs: Additional keyword arguments passed to :class:`zipfile.ZipFile`.

		:rtype: :class:`~.WheelDistribution`
		"""

		path = PathPlus(path)
		name, version, *_ = _parse_wheel_filename(path)
		wheel_zip = handy_archives.ZipFile(path, 'r', **kwargs)

		return cls(name, version, path, wheel_zip)

	def __enter__(self: _WD) -> _WD:
		return self

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self.wheel_zip.close()

	def read_file(self, filename: str) -> str:
		"""
		Read a file from the ``*.dist-info`` directory and return its content.

		:param filename:
		"""

		dist_info = f"{self.name}-{self.version}.dist-info"
		try:
			return self.wheel_zip.read_text(posixpath.join(dist_info, filename))
		except FileNotFoundError as fnf_e:
			try:
				dist_info = _get_dist_info_path(self)
			except _NoDistInfoFound:
				raise fnf_e

			return self.wheel_zip.read_text(posixpath.join(dist_info, filename))

	def has_file(self, filename: str) -> bool:
		"""
		Returns whether the ``*.dist-info`` directory contains a file named ``filename``.

		:param filename:
		"""

		dist_info = f"{self.name}-{self.version}.dist-info"

		if posixpath.join(dist_info, filename) in self.wheel_zip.namelist():
			return True
		else:
			try:
				dist_info = _get_dist_info_path(self)
			except _NoDistInfoFound:
				return False
			else:
				return posixpath.join(dist_info, filename) in self.wheel_zip.namelist()

	def get_wheel(self) -> MetadataMapping:
		"""
		Returns the content of the ``*.dist-info/WHEEL`` file.

		:raises FileNotFoundError: if the file does not exist.
		"""

		return wheel.loads(self.read_file("WHEEL"))

	def get_record(self) -> List[RecordEntry]:
		"""
		Returns the parsed content of the ``*.dist-info/RECORD`` file, or :py:obj:`None` if the file does not exist.

		:returns: A :class:`dist_meta.record.RecordEntry` object for each line in the record
			(i.e. each file in the distribution).
			This includes files in the ``*.dist-info`` directory.

		:raises FileNotFoundError: if the file does not exist.
		"""

		content = self.read_file("RECORD").splitlines()
		output = []

		for line in csv_reader(content):
			name, hash_, size_str, *_ = line
			entry = RecordEntry(
					name,
					hash=FileHash.from_string(hash_) if hash_ else None,
					size=int(size_str) if size_str else None,
					)
			output.append(entry)

		return output


def iter_distributions(path: Optional[Iterable[PathLike]] = None) -> Iterator[Distribution]:
	"""
	Returns an iterator over installed distributions on ``path``.

	:param path: The directories entries to search for distributions in.
	:default path: :py:data:`sys.path`
	"""

	if path is None:  # pragma: no cover
		path = sys.path

	# Distributions found earlier in path will shadow those with the same name found later.
	# If these distributions used different module names, it may actually be possible to import both,
	# but in most cases this shadowing will be correct.
	distro_names_seen = set()

	for folder in map(PathPlus, path):
		if not folder.is_dir():
			continue

		for subdir in _iter_dist_infos(folder):

			if subdir.name[0] == '~':
				# Temporary directory created by pip
				continue

			distro = Distribution.from_path(subdir)

			normalized_name = _canonicalize(distro.name)

			if normalized_name in distro_names_seen:
				continue

			distro_names_seen.add(normalized_name)

			yield distro


def get_distribution(
		name: str,
		path: Optional[Iterable[PathLike]] = None,
		) -> Distribution:
	"""
	Returns a :class:`~.Distribution` instance for the distribution with the given name.

	:param name:
	:param path: The directories entries to search for distributions in.
	:default path: :py:data:`sys.path`

	:rtype:
	"""

	for distro in iter_distributions(path=path):
		if _canonicalize(distro.name) == _canonicalize(name):
			return distro

	raise DistributionNotFoundError(name)


class DistributionNotFoundError(ValueError):
	"""
	Raised when a distribution cannot be located.
	"""


class _NoDistInfoFound(Exception):
	pass


@functools.lru_cache()
def _get_dist_info_path(dist: WheelDistribution) -> str:
	"""
	Find the name of the dist-info directory, case insensitive and allowing unnormalised versions.

	:param dist:

	:raises _NoDistInfoFound: If no dist-info directory is found, or the version/name don't match.
	"""

	casefolded_dist_name = dist.name.casefold()

	for filename in dist.wheel_zip.namelist():
		if ".dist-info" in filename:
			# Might be the directory we're looking for
			with suppress(Exception):
				# Ignore parsing errors
				dist_info_dir = filename.split('/', 1)[0]

				# pylint: disable=dotted-import-in-loop,loop-invariant-statement
				distro_name_version, extension = posixpath.splitext(dist_info_dir)
				if extension != ".dist-info":
					continue

				# pylint: enable=dotted-import-in-loop,loop-invariant-statement

				name, version = divide(distro_name_version, '-')
				if name.casefold() == casefolded_dist_name:
					actual_version = _parse_version(version)
					if actual_version == dist.version:
						dist_info = f"{name}-{version}.dist-info"
						return dist_info

	# path not found
	raise _NoDistInfoFound


def packages_distributions(path: Optional[Iterable[PathLike]] = None) -> Mapping[str, List[str]]:
	"""
	Returns a mapping of top-level packages to a list of distributions which provide them.

	The same top-level package may be provided by multiple distributions,
	especially in the case of namespace packages.

	:param path: The directories entries to search for distributions in.
	:default path: :py:data:`sys.path`

	.. versionadded:: 0.7.0

	:bold-title:`Example:`

	.. code-block:: pycon

		>>> import collections.abc
		>>> pkgs = packages_distributions()
		>>> all(isinstance(dist, collections.abc.Sequence) for dist in pkgs.values())
		True

	"""

	if path is None:  # pragma: no cover
		path = sys.path

	pkg_to_dist = collections.defaultdict(set)

	for dist in iter_distributions(path):
		dist_name = dist.get_metadata()["Name"]
		assert dist_name is not None
		record = dist.get_record() or ()

		for file in record:
			if file.suffix == ".py":

				if ".." in file.parts:
					# File outside of site-packages (e.g. in venv/bin)
					continue

				if len(file.parts) > 1:
					# Package
					pkg = file.parts[0]
				else:
					# Single file module
					pkg = file.stem

				pkg_to_dist[pkg].add(dist_name)

	return {k: sorted(v) for k, v in pkg_to_dist.items()}
