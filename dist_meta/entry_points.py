#!/usr/bin/env python3
#
#  entry_points.py
"""
Parser and emitter for ``entry_points.txt``.

.. note::

	The functions in this module will only parse well-formed ``entry_points.txt`` files,
	and may return unexpected values if passed malformed input.
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
#  Parts based on https://github.com/python/importlib_metadata
#  Copyright 2017-2019 Jason R. Coombs, Barry Warsaw
#  Licensed under the Apache License, Version 2.0
#
#  EntryPoint based on https://github.com/takluyver/entrypoints
#  Copyright (c) 2015 Thomas Kluyver and contributors
#  MIT Licensed
#

# stdlib
import importlib
import re
from itertools import groupby
from typing import Dict, Iterable, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple, TypeVar, Union

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.typing import PathLike
from domdf_python_tools.utils import divide

# this package
from dist_meta._utils import _cache
from dist_meta.distributions import Distribution

__all__ = (
		"lazy_load",
		"lazy_loads",
		"load",
		"loads",
		"dump",
		"dumps",
		"get_entry_points",
		"get_all_entry_points",
		"EntryPoint",
		)

_EP = TypeVar("_EP", bound="EntryPoint")

#: Type hint for a lazily evaluated iterator of entry points.
EntryPointIterator = Iterator[Tuple[str, Iterator[Tuple[str, str]]]]

#: Type hint for a mapping of entry point groups to mappings of entry point names to entry point objects.
EntryPointMap = Dict[str, Dict[str, str]]


class _Section:

	def __init__(self):
		self.section: Optional[str] = None

	def __call__(self, line: str) -> Optional[str]:
		if line.startswith('[') and line.endswith(']'):
			# new section
			self.section = line.strip("[]")
			return None

		return self.section


def _parse_value(line: str) -> Tuple[str, str]:
	name, obj = divide(line, '=')
	return name.strip(), obj.strip()


def lazy_loads(rawtext: str) -> EntryPointIterator:
	"""
	Parse the entry points from the given text lazily.

	:param rawtext:

	:returns: An iterator over ``(group, entry_point)`` tuples, where ``entry_point``
		is an iterator over ``(name, object)`` tuples.
	"""

	lines = filter(None, map(str.strip, rawtext.splitlines()))

	for section, values in groupby(lines, _Section()):
		if section is not None:
			yield section, map(_parse_value, values)


def lazy_load(filename: PathLike) -> EntryPointIterator:
	"""
	Parse the entry points from the given file lazily.

	:param filename:

	:returns: An iterator over ``(group, entry_point)`` tuples, where ``entry_point``
		is an iterator over ``(name, object)`` tuples.
	"""

	filename = PathPlus(filename)
	return lazy_loads(filename.read_text())


@_cache
def loads(rawtext: str) -> EntryPointMap:
	"""
	Parse the entry points from the given text.

	:param rawtext:

	:returns: A mapping of entry point groups to entry points.

		Entry points in each group are contained in a dictionary mapping entry point names to objects.

		:class:`dist_meta.entry_points.EntryPoint` objects can be constructed as follows:

		.. code-block:: python

			for name, epstr in distro.get_entry_points().get("console_scripts", {}).items():
				EntryPoint(name, epstr)
	"""

	eps = lazy_loads(rawtext)
	return {k: dict(v) for k, v in eps}


def load(filename: PathLike) -> EntryPointMap:
	"""
	Parse the entry points from the given file.

	:param filename:

	:returns: A mapping of entry point groups to entry points.

		Entry points in each group are contained in a dictionary mapping entry point names to objects.

		:class:`dist_meta.entry_points.EntryPoint` objects can be constructed as follows:

		.. code-block:: python

			for name, epstr in distro.get_entry_points().get("console_scripts", {}).items():
				EntryPoint(name, epstr)
	"""

	filename = PathPlus(filename)
	return loads(filename.read_text())


def dumps(entry_points: Union[EntryPointMap, Dict[str, Sequence["EntryPoint"]]]) -> str:
	"""
	Construct an ``entry_points.txt`` file for the given grouped entry points.

	:param entry_points:  A mapping of entry point groups to entry points.

		Entry points in each group are contained in a dictionary mapping entry point names to objects,
		or in a list of :class:`~.EntryPoint` objects.
	"""

	output = StringList()

	for group, group_data in entry_points.items():
		output.append(f"[{group}]")

		for name in group_data:
			if isinstance(name, EntryPoint):
				output.append(f"{name.name} = {name.value}")
			else:
				output.append(f"{name} = {group_data[name]}")  # type: ignore[call-overload]

		output.blankline(ensure_single=True)

	return str(output)


def dump(
		entry_points: Union[EntryPointMap, Dict[str, Sequence["EntryPoint"]]],
		filename: PathLike,
		) -> int:
	"""
	Construct an ``entry_points.txt`` file for the given grouped entry points, and write it to ``filename``.

	:param entry_points:  A mapping of entry point groups to entry points.

		Entry points in each group are contained in a dictionary mapping entry point names to objects,
		or in a list of :class:`~.EntryPoint` objects.

	:param filename:
	"""

	filename = PathPlus(filename)
	return filename.write_text(dumps(entry_points))


def get_entry_points(
		group: str,
		path: Optional[Iterable[PathLike]] = None,
		) -> Iterator["EntryPoint"]:
	"""
	Returns an iterator over :class:`entrypoints.EntryPoint` objects in the given group.

	:param group:
	:param path: The directories entries to search for distributions in.
	:default path: :py:data:`sys.path`
	"""

	# this package
	from dist_meta.distributions import iter_distributions

	for distro in iter_distributions(path=path):

		eps = distro.get_entry_points()

		if group in eps:
			for name, epstr in eps[group].items():
				yield EntryPoint(name, epstr, group=group, distro=distro)


def get_all_entry_points(path: Optional[Iterable[PathLike]] = None, ) -> Dict[str, List["EntryPoint"]]:
	"""
	Returns a mapping of entry point groups to entry points for all installed distributions.

	:param path: The directories entries to search for distributions in.
	:default path: :py:data:`sys.path`
	"""

	# this package
	from dist_meta.distributions import iter_distributions

	grouped_eps: Dict[str, List[EntryPoint]] = {}

	for distro in iter_distributions(path=path):

		eps = distro.get_entry_points()

		for group_name in eps:
			group = grouped_eps.setdefault(group_name, [])

			for name, epstr in eps[group_name].items():  # pylint: disable=use-list-copy
				group.append(EntryPoint(name, epstr, group_name, distro))

	return grouped_eps


_entry_point_pattern = re.compile(
		r"""
(?P<modulename>\w+(\.\w+)*)
(:(?P<objectname>\w+(\.\w+)*))?
\s*
(\[(?P<extras>.+)])?
$
""",
		re.VERBOSE
		)


class EntryPoint(NamedTuple):
	"""
	Represents a single entry point.
	"""

	#: The name of the entry point.
	name: str

	#: The value of the entry point, in the form ``module.submodule:attribute``.
	value: str

	#: The group the entry point belongs to.
	group: Optional[str] = None

	#: The distribution the entry point belongs to.
	distro: Optional["Distribution"] = None

	def load(self) -> object:
		"""
		Load the object referred to by this entry point.

		If only a module is indicated by the value, return that module.
		Otherwise, return the named object.
		"""

		match = _entry_point_pattern.match(self.value)
		if not match:
			raise ValueError(f"Malformed entry point {self.value!r}")

		module_name, object_name = match.group("modulename", "objectname")
		obj = importlib.import_module(module_name)

		if object_name:
			for attr in object_name.split('.'):
				obj = getattr(obj, attr)

		return obj

	@property
	def extras(self) -> List[str]:
		"""
		Returns the list of extras associated with the entry point.
		"""

		match = _entry_point_pattern.match(self.value)
		if not match:
			raise ValueError(f"Malformed entry point {self.value!r}")

		extras = match.group("extras")

		if extras is not None:
			return re.split(r',\s*', extras)

		return []

	@property
	def module(self) -> str:
		"""
		The module component of :class:`self.value <.EntryPoint>`.
		"""

		# TODO: proper xref

		match = _entry_point_pattern.match(self.value)
		if not match:
			raise ValueError(f"Malformed entry point {self.value!r}")

		return match.group("modulename")

	@property
	def attr(self) -> str:
		"""
		The object/attribute component of :class:`self.value <.EntryPoint>`.

		:rtype:

		.. latex:clearpage::
		"""

		# TODO: proper xref

		match = _entry_point_pattern.match(self.value)
		if not match:
			raise ValueError(f"Malformed entry point {self.value!r}")

		return match.group("objectname")

	@classmethod
	def from_mapping(
			cls,
			mapping: Mapping[str, str],
			*,
			group: Optional[str] = None,
			distro: Optional["Distribution"] = None,
			) -> List["EntryPoint"]:
		"""
		Returns a list of :class:`~.EntryPoint` objects constructed from values in ``mapping``.

		:param mapping: A mapping of entry point names to values,
			where values are in the form ``module.submodule:attribute``.
		:param group: The group the entry points belong to.
		:param distro: The distribution the entry points belong to.
		"""

		return [EntryPoint(name, value, group, distro) for name, value in mapping.items()]
