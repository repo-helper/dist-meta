# stdlib
from typing import List

# 3rd party
import pytest
from coincidence import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from dist_meta import metadata
from dist_meta.metadata import MissingFieldError
from dist_meta.metadata_mapping import MetadataMapping


@pytest.fixture()
def example_metadata() -> str:
	return (PathPlus(__file__).parent / "example_metadata").read_text()


def test_loads(
		example_metadata: str,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	fields = metadata.loads(example_metadata)

	advanced_data_regression.check(fields.keys())
	assert fields["Metadata-Version"] == "2.1"
	assert fields["Name"] == "cawdrey"
	assert fields["Version"] == "0.4.2"
	assert fields["Summary"] == "Several useful custom dictionaries for Python 📖 🐍"
	assert fields["Home-page"] == "https://github.com/domdfcoding/cawdrey"
	assert fields["Author"] == "Dominic Davis-Foster"
	assert fields["Author-email"] == "dominic@davis-foster.co.uk"
	assert fields["License"] == "GNU Lesser General Public License v3 or later (LGPLv3+)"
	assert fields.get_all("Project-URL") == [
			"Documentation, https://cawdrey.readthedocs.io/en/latest",
			"Issue Tracker, https://github.com/domdfcoding/cawdrey/issues",
			"Source Code, https://github.com/domdfcoding/cawdrey",
			]
	assert fields[
			"Keywords"
			] == "frozenordereddict,orderedfrozendict,frozen,immutable,frozendict,dict,dictionary,map,Mapping,MappingProxyType,Counter"
	assert fields.get_all("Platform") == ["Windows", "macOS", "Linux"]

	assert fields["Requires-Python"] == ">=3.6.1"
	assert fields["Description-Content-Type"] == "text/x-rst"
	assert fields.get_all("Requires-Dist") == ["domdf-python-tools (>=1.1.0)", "typing-extensions (>=3.7.4.3)"]

	assert fields["Provides-Extra"] == "all"

	advanced_file_regression.check(fields["Description"])


def test_load(
		example_metadata: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "METADATA").write_text(example_metadata)
	fields = metadata.load(tmp_pathplus / "METADATA")

	advanced_data_regression.check(fields.keys())
	assert fields["Metadata-Version"] == "2.1"
	assert fields["Name"] == "cawdrey"
	assert fields["Version"] == "0.4.2"
	assert fields["Summary"] == "Several useful custom dictionaries for Python 📖 🐍"
	assert fields["Home-page"] == "https://github.com/domdfcoding/cawdrey"
	assert fields["Author"] == "Dominic Davis-Foster"
	assert fields["Author-email"] == "dominic@davis-foster.co.uk"
	assert fields["License"] == "GNU Lesser General Public License v3 or later (LGPLv3+)"
	assert fields.get_all("Project-URL") == [
			"Documentation, https://cawdrey.readthedocs.io/en/latest",
			"Issue Tracker, https://github.com/domdfcoding/cawdrey/issues",
			"Source Code, https://github.com/domdfcoding/cawdrey",
			]
	assert fields[
			"Keywords"
			] == "frozenordereddict,orderedfrozendict,frozen,immutable,frozendict,dict,dictionary,map,Mapping,MappingProxyType,Counter"
	assert fields.get_all("Platform") == ["Windows", "macOS", "Linux"]

	assert fields["Requires-Python"] == ">=3.6.1"
	assert fields["Description-Content-Type"] == "text/x-rst"
	assert fields.get_all("Requires-Dist") == ["domdf-python-tools (>=1.1.0)", "typing-extensions (>=3.7.4.3)"]

	assert fields["Provides-Extra"] == "all"

	advanced_file_regression.check(fields["Description"])


def test_load_no_version(tmp_pathplus: PathPlus):
	(tmp_pathplus / "METADATA").write_lines([
			"Generator: bdist_wheel (0.36.2)",
			"Name: cawdrey",
			"Version: 0.4.2",
			"Home-page: https://github.com/domdfcoding/cawdrey",
			])

	with pytest.raises(MissingFieldError, match=f"No 'Metadata-Version' field was provided."):
		metadata.load(tmp_pathplus / "METADATA")


def test_dumps(advanced_file_regression: AdvancedFileRegressionFixture):
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	advanced_file_regression.check(metadata.dumps(fields), extension='')


def test_dumps_license_expression_file(advanced_file_regression: AdvancedFileRegressionFixture):
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"
	fields["License-Expression"] = "MIT OR Apache-2.0"
	fields["License-File"] = "LICENSE"
	fields["License-File"] = "COPYING"

	advanced_file_regression.check(metadata.dumps(fields), extension='')


def test_dumps_description(advanced_file_regression: AdvancedFileRegressionFixture):
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"
	fields["Description"] = "This is the body\n\nIt can have multiple lines\n\t\tand indents"

	advanced_file_regression.check(metadata.dumps(fields), extension='')


def test_dump(
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	metadata.dump(fields, tmp_pathplus / "METADATA")
	advanced_file_regression.check_file(tmp_pathplus / "METADATA")


def test_dumps_version_too_low():
	fields = MetadataMapping()
	fields["Metadata-Version"] = "1.1"
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	with pytest.raises(ValueError, match="'dump_metadata' only supports metadata version 2.1 and above."):
		metadata.dumps(fields)


def test_dump_no_meta_version(tmp_pathplus: PathPlus):
	fields = MetadataMapping()
	fields["Name"] = "cawdrey"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	with pytest.raises(MissingFieldError, match=f"No 'Metadata-Version' field was provided."):
		metadata.dump(fields, tmp_pathplus / "METADATA")

	assert not (tmp_pathplus / "METADATA").exists()


def test_dumps_no_name():
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Version"] = "0.4.2"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	with pytest.raises(MissingFieldError, match="No 'Name' field was provided."):
		metadata.dumps(fields)


def test_dumps_no_version():
	fields = MetadataMapping()
	fields["Metadata-Version"] = "2.1"
	fields["Name"] = "cawdrey"
	fields["Home-page"] = "https://github.com/domdfcoding/cawdrey"
	fields["Platform"] = "Windows"
	fields["Platform"] = "macOS"
	fields["Platform"] = "Linux"

	with pytest.raises(MissingFieldError, match="No 'Version' field was provided."):
		metadata.dumps(fields)


def test_loads_description_as_key_pipe():
	fields = metadata.loads(
			'\n'.join([
					"Metadata-Version: 2.1",
					"Name: BeagleVote",
					"version: 1.0a2",
					"Description: This project provides powerful math functions",
					"        |For example, you can use `sum()` to sum numbers:",
					"        |",
					"        |Example::",
					"        |",
					"        |    >>> sum(1, 2)",
					"        |    3",
					"        |",
					])
			)

	assert fields["Metadata-Version"] == "2.1"
	assert fields["Name"] == "BeagleVote"
	assert fields["Version"] == "1.0a2"
	assert fields["Description"] == '\n'.join([
			"This project provides powerful math functions",
			"For example, you can use `sum()` to sum numbers:",
			'',
			"Example::",
			'',
			"    >>> sum(1, 2)",
			"    3",
			'',
			])


def test_loads_description_as_key_spaces():
	# Not to spec, but how setuptools and distutils do it
	fields = metadata.loads(
			'\n'.join([
					"Metadata-Version: 2.1",
					"Name: BeagleVote",
					"version: 1.0a2",
					"Description: This project provides powerful math functions",
					"        For example, you can use `sum()` to sum numbers:",
					"        ",
					"        Example::",
					"        ",
					"            >>> sum(1, 2)",
					"            3",
					"        ",
					])
			)

	assert fields["Metadata-Version"] == "2.1"
	assert fields["Name"] == "BeagleVote"
	assert fields["Version"] == "1.0a2"
	assert fields["Description"] == '\n'.join([
			"This project provides powerful math functions",
			"For example, you can use `sum()` to sum numbers:",
			'',
			"Example::",
			'',
			"    >>> sum(1, 2)",
			"    3",
			'',
			])


@pytest.mark.parametrize(
		"lines, wsp, expected",
		[
				(["hello", "world"], '\t', ["hello", "world"]),
				(["\thello", "\tworld"], '\t', ["hello", "world"]),
				(["hello", "\tworld"], '\t', ["hello", "world"]),
				(["  hello", "  world"], '\t', ["  hello", "  world"]),
				(["|hello", "|world"], '\t', ["|hello", "|world"]),
				(["  hello", "  world"], ' ', ["hello", "world"]),
				(["hello", "  world"], ' ', ["hello", "world"]),
				(["  hello", "world"], ' ', ["  hello", "world"]),
				(["|hello", "|world"], '|', ["hello", "world"]),
				(["hello", "|world"], '|', ["hello", "world"]),
				(["|hello", "world"], '|', ["|hello", "world"]),
				]
		)
def test_clean_desc(lines: List[str], wsp: str, expected: List[str]):
	assert (metadata._clean_desc(lines, wsp) == expected)
