#!/usr/bin/env python3
#
#  _utils.py
"""
Private utility functions.
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
import functools
import os
import pathlib
import re
from typing import Callable, Iterator, Tuple, TypeVar

# 3rd party
from domdf_python_tools.paths import PathPlus
from packaging.utils import InvalidWheelFilename, canonicalize_name
from packaging.version import Version

_escaped_name_re = re.compile(r"^[\w\d._]*$", re.UNICODE)

SHOULD_CACHE = int(os.environ.get("DIST_META_CACHE", 1))

_C = TypeVar("_C", bound=Callable)


def _cache(func: _C) -> _C:
	if SHOULD_CACHE:
		return functools.lru_cache()(func)  # type: ignore[return-value]
	else:  # pragma: no cover
		return func


@_cache
def _canonicalize(name: str) -> str:
	return canonicalize_name(name)


@_cache
def _parse_wheel_filename(filename: pathlib.PurePath) -> Tuple[str, Version]:
	# From https://github.com/pypa/packaging
	# This software is made available under the terms of *either* of the licenses
	# found in LICENSE.APACHE or LICENSE.BSD. Contributions to this software is made
	# under the terms of *both* these licenses.

	if not filename.suffix == ".whl":
		raise InvalidWheelFilename(f"Invalid wheel filename (extension must be '.whl'): {filename}")

	stem = filename.stem
	dashes = stem.count('-')
	if dashes not in (4, 5):
		raise InvalidWheelFilename(f"Invalid wheel filename (wrong number of parts): {filename}")

	parts = stem.split('-', dashes - 2)
	name = parts[0]
	# See PEP 427 for the rules on escaping the project name
	if "__" in name or _escaped_name_re.match(name) is None:
		raise InvalidWheelFilename(f"Invalid project name: {name!r}")

	version = _parse_version(parts[1])

	return name, version


def _iter_dist_infos(basedir: PathPlus) -> Iterator[os.DirEntry]:
	subdir: os.DirEntry
	with os.scandir(os.fspath(basedir)) as sd:
		for subdir in sd:
			if not subdir.is_dir():
				continue

			if not subdir.name.endswith(".dist-info"):
				continue

			yield subdir


@_cache
def _parse_version(version: str) -> Version:
	return Version(version)
