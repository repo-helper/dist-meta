#!/usr/bin/env python
#
#  metadata_mapping.py
"""
:class:`collections.abc.MutableMapping` which supports duplicate, case-insensitive keys.

.. caution::

	These are pretty low-level classes. You probably don't need to use these directly
	unless you're customising the ``METADATA`` file creation or parsing.

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
#  Based on CPython.
#  Licensed under the Python Software Foundation License Version 2.
#  Copyright © 2001-2021 Python Software Foundation. All rights reserved.
#  Copyright © 2000 BeOpen.com. All rights reserved.
#  Copyright © 1995-2000 Corporation for National Research Initiatives. All rights reserved.
#  Copyright © 1991-1995 Stichting Mathematisch Centrum. All rights reserved.
#

# stdlib
from typing import Iterator, List, MutableMapping, Optional, Tuple, TypeVar, Union, cast, overload

# 3rd party
from domdf_python_tools.stringlist import DelimitedList, StringList

__all__ = ("MetadataMapping", "MetadataEmitter")

_T = TypeVar("_T")


class MetadataMapping(MutableMapping[str, str]):
	"""
	Provides a :class:`~collections.abc.MutableMapping` interface to a list of fields,
	such as those used for Python `core metadata`_.

	.. _core metadata: https://packaging.python.org/specifications/core-metadata/

	.. seealso:: :class:`email.message.Message` and :class:`email.message.EmailMessage`

	Implements the :class:`~collections.abc.MutableMapping` interface,
	which assumes there is exactly one occurrence of the field per mapping.
	Some fields do in fact appear multiple times,
	and for those fields you must use the :meth:`~.MetadataMapping.get_all` method
	to obtain all values for that field.
	"""  # noqa: D400

	def __init__(self):
		self._fields: List[Tuple[str, str]] = []

	#
	# MAPPING INTERFACE (partial)
	#

	def __len__(self) -> int:
		"""
		Return the total number of keys, including duplicates.
		"""

		return len(self._fields)

	def __getitem__(self, name: str) -> str:
		"""
		Get a field value.

		.. latex:vspace:: -10px

		.. note::

			If the field appears multiple times, exactly which occurrence gets returned is undefined.
			Use the :meth:`~.MetadataMapping.get_all` method to get all values matching a field name.

		.. latex:vspace:: -20px

		:param name:
		"""

		if name not in self:
			raise KeyError(name)

		return cast(str, self.get(name))

	def __setitem__(self, name: str, val: str) -> None:
		"""
		Set the value of a field.

		.. attention:

			This does not overwrite existing fields with the same field name.
			Use :meth:`MetadataMapping.__delitem__` first to delete any existing fields.

		:param name:
		:param val:
		"""

		self._fields.append((name, val))

	def __delitem__(self, name: str) -> None:
		"""
		Delete all occurrences of a field, if present.

		Does not raise an exception if the field is missing.

		:param name:
		"""

		name = name.lower()
		self._fields = [(k, v) for k, v in self._fields if k.lower() != name]

	def __contains__(self, name: object) -> bool:
		"""
		Returns whether ``name`` is in the :class:`~.MetadataMapping`.

		:param name:
		"""

		if not isinstance(name, str):
			return False

		name = name.lower()

		for k, v in self._fields:
			if k.lower() == name:
				return True

		return False

	def __iter__(self) -> Iterator[str]:
		"""
		Returns an iterator over the keys in the :class:`~.MetadataMapping`.
		"""

		for field, value in self._fields:
			yield field

	def keys(self) -> List[str]:  # type: ignore[override]
		"""
		Return a list of all field *names*.

		These will be sorted by insertion order, and may contain duplicates.
		Any fields deleted and re-inserted are always appended to the field list.
		"""

		return [k for k, v in self._fields]

	def values(self) -> List[str]:  # type: ignore[override]
		"""
		Return a list of all field *values*.

		These will be sorted by insertion order, and may contain duplicates.
		Any fields deleted and re-inserted are always appended to the field list.
		"""

		return [v for k, v in self._fields]

	def items(self) -> List[Tuple[str, str]]:  # type: ignore[override]
		"""
		Get all the fields and their values.

		These will be sorted by insertion order, and may contain duplicates.
		Any fields deleted and re-inserted are always appended to the field list.
		"""

		return self._fields[:]

	@overload
	def get(self, name: str) -> Optional[str]: ...

	@overload
	def get(self, name: str, default: Union[str, _T]) -> Union[str, _T]: ...

	def get(self, name: str, default=None) -> str:  # noqa: MAN001
		"""
		Get a field value.

		Like :meth:`~.MetadataMapping.__getitem__`,
		but returns ``default`` instead of :py:obj:`None` when the field is missing.

		.. note::

			If the field appears multiple times, exactly which occurrence gets returned is undefined.
			Use the :meth:`~.MetadataMapping.get_all` method to get all values matching a field name.

		.. latex:vspace:: -10px

		:param name:
		:param default:
		"""

		name = name.lower()

		for key, val in self._fields:
			if key.lower() == name:
				return val

		return default

	#
	# Additional useful stuff
	#

	@overload
	def get_all(self, name: str) -> Optional[List[str]]: ...

	@overload
	def get_all(self, name: str, default: Union[str, _T]) -> Union[List[str], _T]: ...

	def get_all(self, name: str, default=None):  # noqa: MAN001,MAN002
		"""
		Return a list of all the values for the named field.

		These will be sorted in the order they appeared in the original message,
		and may contain duplicates.
		Any fields deleted and re-inserted are always appended to the field list.

		If no such fields exist, ``default`` is returned.

		:param name:
		:param default:
		"""

		name = name.lower()
		values = [val for key, val in self._fields if key.lower() == name]

		if not values:
			return default

		return values

	def __repr__(self) -> str:
		"""
		Return a string representation of the :class:`~.MetadataMapping`.
		"""

		items = DelimitedList([f"{k!r}: {v!r}" for k, v in self.items()])
		as_dict = f"{{{items:, }}}"

		return f"<{self.__class__.__name__}({as_dict})>"

	def replace(self, name: str, value: str) -> None:
		"""
		Replace the value of the first matching field, retaining header order and case.

		:raises KeyError: If no matching field was found.
		"""

		for i, (key, val) in enumerate(self._fields):
			if key.lower() == name.lower():
				self._fields[i] = (name, value)
				break
		else:
			raise KeyError(name)


class MetadataEmitter(StringList):
	"""
	Used to construct ``METADATA``, ``WHEEL`` and other email field-like files.

	:param fields: The fields the file is being constructed from.

	.. autosummary-widths:: 1/3
	"""

	def __init__(self, fields: MetadataMapping):
		self.fields = fields
		super().__init__()

	def add_single(self, field_name: str) -> None:
		"""
		Add a single value for the field with the given name.

		:param field_name:
		"""

		if field_name in self.fields:
			self.append(f"{field_name}: {self.fields[field_name]}")

	def add_multiple(self, field_name: str) -> None:
		"""
		Add all values for the "multiple use" field with the given name.

		:param field_name:
		"""

		if field_name in self.fields:
			for value in self.fields.get_all(field_name, ()):  # pylint: disable=use-list-copy
				self.append(f"{field_name}: {value}")

	def add_body(self, body: str) -> None:
		"""
		Add a body to the file.

		In an email message this is the message content itself.

		:param body:
		"""

		self.blankline(ensure_single=True)
		self.blankline()
		self.append(body)
		self.blankline(ensure_single=True)
