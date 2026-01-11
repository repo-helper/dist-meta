# stdlib
from textwrap import dedent
from typing import Tuple

# 3rd party
import pytest
from coincidence import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from dist_meta import wheel
from dist_meta.metadata import MissingFieldError
from dist_meta.metadata_mapping import MetadataMapping


def test_loads():
	wheel_content = dedent(
			"""
	Wheel-Version: 1.0
	Generator: bdist_wheel (0.36.2)
	Root-Is-Purelib: true
	Tag: py3-none-any
	Tag: py2-none-any
	\r""",
			)

	fields = wheel.loads(wheel_content)
	assert fields.keys() == ["Wheel-Version", "Generator", "Root-Is-Purelib", "Tag", "Tag"]
	assert fields["Wheel-Version"] == "1.0"
	assert fields["Generator"] == "bdist_wheel (0.36.2)"
	assert fields["Root-Is-Purelib"] == "true"
	assert fields.get_all("Tag") == ["py3-none-any", "py2-none-any"]


def test_load(tmp_pathplus: PathPlus):
	(tmp_pathplus / "WHEEL").write_lines([
			"Wheel-Version: 1.0",
			"Generator: bdist_wheel (0.36.2)",
			"Root-Is-Purelib: true",
			"Tag: py3-none-any",
			"Tag: py2-none-any",
			])

	fields = wheel.load(tmp_pathplus / "WHEEL")
	assert fields.keys() == ["Wheel-Version", "Generator", "Root-Is-Purelib", "Tag", "Tag"]
	assert fields["Wheel-Version"] == "1.0"
	assert fields["Generator"] == "bdist_wheel (0.36.2)"
	assert fields["Root-Is-Purelib"] == "true"
	assert fields.get_all("Tag") == ["py3-none-any", "py2-none-any"]


def test_load_no_version(tmp_pathplus: PathPlus):
	(tmp_pathplus / "WHEEL").write_lines([
			"Generator: bdist_wheel (0.36.2)",
			"Root-Is-Purelib: true",
			"Tag: py3-none-any",
			"Tag: py2-none-any",
			])

	with pytest.raises(MissingFieldError, match="No 'Wheel-Version' field was provided."):
		wheel.load(tmp_pathplus / "WHEEL")


fields = MetadataMapping()
fields["Wheel-Version"] = "1.0"
fields["Generator"] = "bdist_wheel (0.36.2)"
fields["Root-Is-Purelib"] = "true"
fields["Tag"] = "py3-none-any"
fields["Tag"] = "py2-none-any"

fields_no_root_is_purelib = MetadataMapping()
fields_no_root_is_purelib["Wheel-Version"] = 1.0  # type: ignore[assignment]
fields_no_root_is_purelib["Generator"] = "bdist_wheel (0.36.2)"
fields_no_root_is_purelib["Tag"] = "py3-none-any"
fields_no_root_is_purelib["Tag"] = "py2-none-any"

fields_dict = {
		"Wheel-Version": 1.0,
		"Generator": "bdist_wheel (0.36.2)",
		"Root-Is-Purelib": True,
		"Tag": ["py3-none-any", "py2-none-any"],
		}

fields_dict_no_root_is_purelib = {
		"Wheel-Version": "1.0",
		"Generator": "bdist_wheel (0.36.2)",
		"Tag": ["py3-none-any", "py2-none-any"],
		}


@pytest.mark.parametrize(
		"fields",
		[
				pytest.param(fields, id="fields"),
				pytest.param(fields_no_root_is_purelib, id="fields_no_root_is_purelib"),
				pytest.param(fields_dict, id="fields_dict"),
				pytest.param(fields_dict_no_root_is_purelib, id="fields_dict_no_root_is_purelib"),
				],
		)
def test_dumps(fields: MetadataMapping, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(wheel.dumps(fields), extension='')


@pytest.mark.parametrize(
		"fields",
		[
				pytest.param(fields, id="fields"),
				pytest.param(fields_no_root_is_purelib, id="fields_no_root_is_purelib"),
				pytest.param(fields_dict, id="fields_dict"),
				pytest.param(fields_dict_no_root_is_purelib, id="fields_dict_no_root_is_purelib"),
				],
		)
def test_dump(
		fields: MetadataMapping,
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	wheel.dump(fields, tmp_pathplus / "WHEEL")
	advanced_file_regression.check_file(tmp_pathplus / "WHEEL")


def test_dump_no_version(tmp_pathplus: PathPlus):
	fields = MetadataMapping()
	fields["Generator"] = "bdist_wheel (0.36.2)"
	fields["Root-Is-Purelib"] = "true"
	fields["Tag"] = "py3-none-any"
	fields["Tag"] = "py2-none-any"

	with pytest.raises(MissingFieldError, match="No 'Wheel-Version' field was provided."):
		wheel.dump(fields, tmp_pathplus / "WHEEL")

	assert not (tmp_pathplus / "WHEEL").exists()


@pytest.mark.parametrize(
		"generator, expected",
		[
				("bdist_wheel (0.34.2)", ("bdist_wheel", "0.34.2")),
				("bdist_wheel (0.36.2)", ("bdist_wheel", "0.36.2")),
				("bdist_wheel (0.37.0)", ("bdist_wheel", "0.37.0")),
				("poetry 1.0.7", ("poetry", "1.0.7")),
				("poetry-core 1.1.0", ("poetry-core", "1.1.0")),
				("skbuild 0.15.0", ("skbuild", "0.15.0")),
				("hatchling 1.10.0", ("hatchling", "1.10.0")),
				("flit 3.5.1", ("flit", "3.5.1")),
				("flit 3.7.1", ("flit", "3.7.1")),
				("act (2.2)", ("act", "2.2")),
				("foo", ("foo", None)),
				("pdm-pep517 0.12.7", ("pdm-pep517", "0.12.7")),
				],
		)
def test_parse_generator_string(generator: str, expected: Tuple[str, str]):
	assert wheel.parse_generator_string(generator) == expected
