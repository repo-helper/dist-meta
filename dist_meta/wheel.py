#!/usr/bin/env python3
#
#  wheel.py
"""
Parse and create ``*dist-info/WHEEL`` files.
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
from typing import Any, List, Mapping, Optional, Tuple, Union

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from domdf_python_tools.utils import divide, strtobool

# this package
from dist_meta.metadata import MetadataEmitter, MissingFieldError
from dist_meta.metadata_mapping import MetadataMapping

__all__ = ("dump", "dumps", "load", "loads", "parse_generator_string")


def loads(rawtext: str) -> MetadataMapping:
	"""
	Parse a ``WHEEL`` file from the given string.

	:param rawtext:

	:returns: A mapping of the metadata fields, and the long description
	"""

	file_content: List[str] = rawtext.splitlines()
	file_content.reverse()

	fields: MetadataMapping = MetadataMapping()

	while file_content:
		line = file_content.pop()
		if line.strip():
			field_name, field_value = divide(line, ':')
			fields[field_name] = field_value.lstrip()  # pylint: disable=loop-invariant-statement

	if "Wheel-Version" not in fields:
		raise MissingFieldError(f"No 'Wheel-Version' field was provided.")

	return fields


def load(filename: PathLike) -> MetadataMapping:
	"""
	Parse a ``WHEEL`` file from the given file.

	:param filename:

	:returns: A mapping of the metadata fields, and the long description
	"""

	filename = PathPlus(filename)
	return loads(filename.read_text())


def dumps(fields: Union[Mapping[str, Any], MetadataMapping]) -> str:
	"""
	Construct a ``WHEEL`` file from the given fields.

	:param fields: May be a conventional mapping, with ``Root-Is-Purelib`` as a boolean
		and ``Tag`` as a list of strings.
	"""

	output = MetadataEmitter(fields)  # type: ignore[arg-type]

	if "Wheel-Version" in fields:
		output.append(f"Wheel-Version: {float(fields['Wheel-Version'])}")
	else:
		raise MissingFieldError(f"No 'Wheel-Version' field was provided.")

	output.add_single("Generator")

	root_is_purelib = strtobool(fields.get("Root-Is-Purelib", False))
	output.append(f"Root-Is-Purelib: {str(root_is_purelib).lower()}")

	if "Tag" in fields and isinstance(fields, MetadataMapping):
		output.add_multiple("Tag")
	elif "Tag" in fields:
		for value in fields["Tag"]:  # pylint: disable=use-list-copy
			output.append(f"Tag: {value}")

	output.add_single("Build")

	return str(output)


def dump(fields: Union[Mapping[str, Any], MetadataMapping], filename: PathLike) -> int:
	"""
	Construct a ``WHEEL`` file from the given fields, and write it to ``filename``.

	:param fields: May be a conventional mapping, with ``Root-Is-Purelib`` as a boolean
		and ``Tag`` as a list of strings.
	:param filename:
	"""

	filename = PathPlus(filename)
	return filename.write_text(dumps(fields))


def parse_generator_string(generator: str) -> Tuple[str, Optional[str]]:
	"""
	Parse a generator string into its name and version.

	Common forms include:

	* ``name (version)``
	* ``name version``
	* ``name``

	.. versionadded:: 0.6.0

	:param generator: The raw generator string (the ``Generator`` field in ``WHEEL``).

	:return: A tuple of the generator name and its version.
		The version may be :py:obj:`None` if no version could be found.
	"""

	generator = generator.rstrip()

	if ' ' not in generator:
		return generator, None

	name, version = generator.split(' ', 1)
	version = version.lstrip('(').rstrip(')')

	return name, version
