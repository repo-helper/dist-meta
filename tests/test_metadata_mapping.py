# stdlib
from textwrap import dedent

# 3rd party
import pytest
from coincidence import AdvancedFileRegressionFixture

# this package
from dist_meta.metadata_mapping import MetadataEmitter, MetadataMapping


def test_instantiation():
	MetadataMapping()


def test_headermapping():
	h = MetadataMapping()

	# Setitem
	h["foo"] = "bar"

	assert dict(h) == {"foo": "bar"}

	h["Foo"] = "bar"

	assert dict(h) == {"foo": "bar", "Foo": "bar"}
	assert h.keys() == ["foo", "Foo"]

	h["Foo"] = "baz"

	assert dict(h) == {"foo": "bar", "Foo": "bar"}
	assert h.keys() == ["foo", "Foo", "Foo"]
	assert h.values() == ["bar", "bar", "baz"]
	assert h.items() == [("foo", "bar"), ("Foo", "bar"), ("Foo", "baz")]
	assert h.get_all("foo") == ["bar", "bar", "baz"]
	assert list(iter(h)) == ["foo", "Foo", "Foo"]
	assert repr(h) == "<MetadataMapping({'foo': 'bar', 'Foo': 'bar', 'Foo': 'baz'})>"

	# getitem
	assert h["foo"] == "bar"
	assert h["Foo"] == "bar"

	assert "bar" not in h
	assert 42 not in h

	with pytest.raises(KeyError, match="bar"):
		h["bar"]  # pylint: disable=pointless-statement

	# len
	assert len(h) == 3

	# delitem

	h["bar"] = "baz"

	del h["Foo"]
	assert dict(h) == {"bar": "baz"}
	assert repr(h) == "<MetadataMapping({'bar': 'baz'})>"

	assert "Foo" not in h
	assert "foo" not in h


def test_get_default():
	h = MetadataMapping()

	assert h.get("foo", 42) == 42
	assert h.get_all("foo", 42) == 42

	assert h.get("foo") is None
	assert h.get_all("foo") is None


def test_metadata_emitter():
	h = MetadataMapping()
	h["Metadata-Version"] = "2.1"
	h["Name"] = "cawdrey"
	h["Version"] = "0.4.2"
	h["Platform"] = "Windows"
	h["Platform"] = "macOS"
	h["Platform"] = "Linux"

	output = MetadataEmitter(h)

	output.add_single("Metadata-Version")
	assert str(output) == "Metadata-Version: 2.1"

	output.add_single("namE")
	assert str(output) == "Metadata-Version: 2.1\nnamE: cawdrey"

	output.add_single("Version")
	output.add_single("Platform")
	assert str(output) == "Metadata-Version: 2.1\nnamE: cawdrey\nVersion: 0.4.2\nPlatform: Windows"

	output.add_multiple("Platform")
	assert str(output) == dedent(
			"""\
		Metadata-Version: 2.1
		namE: cawdrey
		Version: 0.4.2
		Platform: Windows
		Platform: Windows
		Platform: macOS
		Platform: Linux"""
			)

	output.add_body("This is the body\n\nIt can have multiple lines\n\t\tand indents")
	assert str(output) == dedent(
			"""\
		Metadata-Version: 2.1
		namE: cawdrey
		Version: 0.4.2
		Platform: Windows
		Platform: Windows
		Platform: macOS
		Platform: Linux


		This is the body

		It can have multiple lines
		\t\tand indents
		"""
			)
