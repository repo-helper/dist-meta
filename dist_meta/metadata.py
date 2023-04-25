#!/usr/bin/env python3
#
#  metadata.py
"""
Parse and create ``*dist-info/METADATA`` files.
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
import sys
from typing import List

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from domdf_python_tools.utils import divide

# this package
from dist_meta.metadata_mapping import MetadataEmitter, MetadataMapping

__all__ = ("dump", "dumps", "load", "loads", "MissingFieldError")

DELIMITER = "\n\n"
NEWLINE_MARK = '\uf8ff'


def _clean_desc(lines: List[str], wsp: str) -> List[str]:
	#  Adapted from inspect.cleandoc
	#  Licensed under the Python Software Foundation License Version 2.
	#  Copyright © 2001-2020 Python Software Foundation. All rights reserved.
	#  Copyright © 2000 BeOpen.com. All rights reserved.
	#  Copyright © 1995-2000 Corporation for National Research Initiatives. All rights reserved.
	#  Copyright © 1991-1995 Stichting Mathematisch Centrum. All rights reserved.

	assert len(wsp) == 1

	# Find minimum indentation of any non-blank lines after first line.
	margin = sys.maxsize

	include_first_line = False

	for line in lines[1:]:
		content = len(line.lstrip(wsp))
		if content:
			indent = len(line) - content
			margin = min(margin, indent)

	# Remove indentation.
	if margin < sys.maxsize:
		if lines[0][:margin] == (wsp * margin):
			include_first_line = True

		for i in range(not include_first_line, len(lines)):
			lines[i] = lines[i][margin:]

	return lines


class MissingFieldError(ValueError):
	"""
	Raised when a required field is missing.
	"""


def loads(rawtext: str) -> MetadataMapping:
	"""
	Parse Python core metadata from the given string.

	:param rawtext:

	:returns: A mapping of the metadata fields, and the long description
	"""

	rawtext = rawtext.replace("\r\n", '\n')

	if DELIMITER in rawtext:
		rawtext, body = rawtext.split(DELIMITER, maxsplit=1)
	else:
		body = ''

	# unfold per RFC 5322 § 2.2.3
	rawtext = rawtext.replace("\n\t", f"{NEWLINE_MARK}\t").replace("\n ", f"{NEWLINE_MARK} ")

	file_content: List[str] = rawtext.split('\n')

	fields: MetadataMapping = MetadataMapping()

	for line in file_content:
		if not line:
			continue

		field_name, field_value = divide(line, ':')

		# pylint: disable=loop-global-usage
		if field_name.lower() != "description":
			fields[field_name] = field_value.replace(NEWLINE_MARK, '').lstrip()
		else:
			# Unwrap
			description_lines = field_value.split(NEWLINE_MARK)
			description_lines = _clean_desc(description_lines, ' ')
			description_lines = _clean_desc(description_lines, '\t')
			description_lines = _clean_desc(description_lines, '|')
			# pylint: enable=loop-global-usage

			# pylint: disable=loop-invariant-statement
			fields["Description"] = '\n'.join(description_lines).strip() + '\n'
			# pylint: enable=loop-invariant-statement

	if body.strip():
		if "Description" in fields:
			raise ValueError(
					"A value was given for the 'Description' field "
					"but the body of the file is not empty."
					)
		else:
			fields["Description"] = body.strip() + '\n'

	for required_field in ["Metadata-Version", "Name", "Version"]:
		if required_field not in fields:
			raise MissingFieldError(f"No {required_field!r} field was provided.")

	return fields


def load(filename: PathLike) -> MetadataMapping:
	"""
	Parse Python core metadata from the given file.

	:param filename:

	:returns: A mapping of the metadata fields, and the long description
	"""

	filename = PathPlus(filename)
	return loads(filename.read_text())


def dumps(fields: MetadataMapping) -> str:
	"""
	Construct Python core metadata from the given fields.

	:param fields:

	:rtype:

	.. versionchanged:: 0.4.0

		Added support for the License-Expression and License-File options proposed by :pep:`639`.

	.. latex:clearpage::
	"""

	output = MetadataEmitter(fields)

	if "Metadata-Version" in fields:
		version = float(fields["Metadata-Version"])
		output.append(f"Metadata-Version: {fields['Metadata-Version']}")
	else:
		raise MissingFieldError("No 'Metadata-Version' field was provided.")

	if version < 2.1:
		raise ValueError("'dump_metadata' only supports metadata version 2.1 and above.")

	for required_field in ["Name", "Version"]:
		if required_field in fields:
			output.append(f"{required_field}: {fields[required_field]}")
		else:
			raise MissingFieldError(f"No {required_field!r} field was provided.")

	if version >= 2.2:
		output.add_multiple("Dynamic")

	# General Meta
	output.add_single("Summary")
	output.add_single("Author")
	output.add_single("Author-email")
	output.add_single("Maintainer")
	output.add_single("Maintainer-email")
	output.add_single("License")
	output.add_single("License-Expression")
	output.add_multiple("License-File")
	output.add_single("Keywords")

	# URLs
	output.add_single("Home-page")
	output.add_single("Download-URL")
	output.add_multiple("Project-URL")

	# Platforms
	output.add_multiple("Platform")
	output.add_multiple("Supported-Platform")
	output.add_multiple("Classifier")

	# Requirements
	output.add_single("Requires-Python")
	output.add_multiple("Requires-Dist")
	output.add_multiple("Provides-Extra")
	output.add_multiple("Requires-External")
	output.add_multiple("Provides-Dist")
	output.add_multiple("Obsoletes-Dist")

	# Description
	output.add_single("Description-Content-Type")

	if "Description" in fields:
		output.add_body(fields["Description"])

	return str(output)


def dump(fields: MetadataMapping, filename: PathLike) -> int:
	"""
	Construct Python core metadata from the given fields, and write it to ``filename``.

	:param fields:
	:param filename:
	"""

	filename = PathPlus(filename)
	return filename.write_text(dumps(fields))
