# stdlib
from operator import attrgetter, itemgetter
from textwrap import dedent
from typing import Dict, Iterator, List

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from dist_meta import entry_points

expected_load_output = {"console_scripts": {"py.test": "pytest:console_main", "pytest": "pytest:console_main"}}


@pytest.fixture()
def example_metadata():
	return (PathPlus(__file__).parent / "example_entry_points.txt").read_text()


def test_loads(advanced_data_regression: AdvancedDataRegressionFixture):
	entry_points_content = dedent(
			"""
			[console_scripts]
			py.test = pytest:console_main
			pytest = pytest:console_main
			"""
			)

	assert entry_points.loads(entry_points_content) == expected_load_output


def test_load(tmp_pathplus, advanced_data_regression: AdvancedDataRegressionFixture):
	(tmp_pathplus / "entry_points.txt").write_lines([
			"[console_scripts]",
			"py.test = pytest:console_main",
			"pytest = pytest:console_main",
			])

	assert entry_points.load(tmp_pathplus / "entry_points.txt") == expected_load_output


def test_loads_longer(advanced_data_regression: AdvancedDataRegressionFixture, example_metadata):
	advanced_data_regression.check(entry_points.loads(example_metadata))


def test_load_longer(tmp_pathplus, advanced_data_regression: AdvancedDataRegressionFixture, example_metadata):
	(tmp_pathplus / "entry_points.txt").write_text(example_metadata)
	advanced_data_regression.check(entry_points.load(tmp_pathplus / "entry_points.txt"))


def test_lazy_loads(advanced_data_regression: AdvancedDataRegressionFixture):
	entry_points_content = dedent(
			"""
			[console_scripts]
			py.test = pytest:console_main
			pytest = pytest:console_main
			"""
			)

	eps = entry_points.lazy_loads(entry_points_content)
	assert isinstance(eps, Iterator)

	for group, entries in eps:
		assert isinstance(group, str)
		assert group == "console_scripts"
		assert isinstance(entries, Iterator)

		for name, epstr in entries:
			assert name in {"py.test", "pytest"}
			assert epstr == "pytest:console_main"

	eps = entry_points.lazy_loads(entry_points_content)
	assert {k: dict(v) for k, v in eps} == expected_load_output


def test_lazy_load(tmp_pathplus, advanced_data_regression: AdvancedDataRegressionFixture):
	(tmp_pathplus / "entry_points.txt").write_lines([
			'',
			"[console_scripts]",
			"py.test = pytest:console_main",
			"pytest = pytest:console_main",
			])

	eps = entry_points.lazy_load(tmp_pathplus / "entry_points.txt")

	assert isinstance(eps, Iterator)

	for group, entries in eps:
		assert isinstance(group, str)
		assert group == "console_scripts"
		assert isinstance(entries, Iterator)

		for name, epstr in entries:
			assert name in {"py.test", "pytest"}
			assert epstr == "pytest:console_main"

	eps = entry_points.lazy_load(tmp_pathplus / "entry_points.txt")
	assert {k: dict(v) for k, v in eps} == expected_load_output


def test_loads_bad_syntax(advanced_data_regression: AdvancedDataRegressionFixture):
	entry_points_content = '\n'.join(["py.test = pytest:console_main", "pytest = pytest:console_main"])
	assert entry_points.loads(entry_points_content) == {}


@pytest.mark.parametrize(
		"ep_dict",
		[
				pytest.param({
						"console_scripts": {"py.test": "pytest:console_main", "pytest": "pytest:console_main"}
						},
								id="short"),
				pytest.param({
						"console_scripts": {"spam-cli": "spam:main_cli", "foobar": "foomod:main_bar [bar,baz]"},
						"gui_scripts": {"spam-gui": "spam.gui:main_gui"},
						"spam.magical": {"tomatoes": "spam:main_tomatoes"},
						"pytest11": {"nbval": "nbval.plugin"},
						},
								id="complex"),
				pytest.param({
						"console_scripts": [
								entry_points.EntryPoint("py.test", "pytest:console_main"),
								entry_points.EntryPoint("pytest", "pytest:console_main"),
								],
						},
								id="short_obj"),
				pytest.param({
						"console_scripts": [
								entry_points.EntryPoint("spam-cli", "spam:main_cli"),
								entry_points.EntryPoint("foobar", "foomod:main_bar [bar,baz]"),
								],
						"gui_scripts": [entry_points.EntryPoint("spam-gui", "spam.gui:main_gui")],
						"spam.magical": [entry_points.EntryPoint("tomatoes", "spam:main_tomatoes")],
						"pytest11": [entry_points.EntryPoint("nbval", "nbval.plugin")],
						},
								id="complex_obj"),
				]
		)
def test_dumps(advanced_file_regression: AdvancedFileRegressionFixture, ep_dict):
	advanced_file_regression.check(entry_points.dumps(ep_dict))


@pytest.mark.parametrize(
		"ep_dict",
		[
				pytest.param({
						"console_scripts": {"py.test": "pytest:console_main", "pytest": "pytest:console_main"},
						},
								id="short"),
				pytest.param({
						"console_scripts": {"spam-cli": "spam:main_cli", "foobar": "foomod:main_bar [bar,baz]"},
						"gui_scripts": {"spam-gui": "spam.gui:main_gui"},
						"spam.magical": {"tomatoes": "spam:main_tomatoes"},
						"pytest11": {"nbval": "nbval.plugin"},
						},
								id="complex"),
				]
		)
def test_dump(
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		ep_dict,
		):
	entry_points.dump(ep_dict, tmp_pathplus / "entry_points.txt")
	advanced_file_regression.check_file(tmp_pathplus / "entry_points.txt")


def test_entry_point_class():

	ep = entry_points.EntryPoint(
			name="pytest",
			value="pytest:console_main",
			group="console_scripts",
			)

	assert ep.name == "pytest"
	assert ep.value == "pytest:console_main"
	assert ep.group == "console_scripts"
	assert ep.distro is None

	assert ep.load() is pytest.console_main

	assert ep.extras == []
	assert ep.module == "pytest"
	assert ep.attr == "console_main"


def test_entry_point_class_from_mapping():

	eps = entry_points.EntryPoint.from_mapping(
			{"pytest": "pytest:console_main", "py.test": "pytest:console_main"},
			group="console_scripts",
			)

	ep = eps[0]

	assert ep.name == "pytest"
	assert ep.value == "pytest:console_main"
	assert ep.group == "console_scripts"
	assert ep.distro is None

	assert ep.load() is pytest.console_main

	assert ep.extras == []
	assert ep.module == "pytest"
	assert ep.attr == "console_main"

	ep = eps[1]

	assert ep.name == "py.test"
	assert ep.value == "pytest:console_main"
	assert ep.group == "console_scripts"
	assert ep.distro is None

	assert ep.load() is pytest.console_main

	assert ep.extras == []
	assert ep.module == "pytest"
	assert ep.attr == "console_main"


def test_entry_point_class_extras():

	ep = entry_points.EntryPoint(
			name="pytest",
			value="pytest:console_main [cli]",
			group="console_scripts",
			)

	assert ep.name == "pytest"
	assert ep.value == "pytest:console_main [cli]"
	assert ep.group == "console_scripts"
	assert ep.distro is None

	assert ep.load() is pytest.console_main

	assert ep.extras == ["cli"]
	assert ep.module == "pytest"
	assert ep.attr == "console_main"


@pytest.mark.parametrize("value", ['', "1:", '-', ":console_main", "foo-bar"])
def test_entry_point_class_malformed(value):

	ep = entry_points.EntryPoint(
			name="pytest",
			value=value,
			group="console_scripts",
			)

	assert ep.value == value

	with pytest.raises(ValueError, match="Malformed entry point '.*'"):
		ep.load()

	with pytest.raises(ValueError, match="Malformed entry point '.*'"):
		attrgetter("extras")(ep)

	with pytest.raises(ValueError, match="Malformed entry point '.*'"):
		attrgetter("module")(ep)

	with pytest.raises(ValueError, match="Malformed entry point '.*'"):
		attrgetter("attr")(ep)


def test_get_entry_points(
		fake_virtualenv: List[PathPlus],
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	all_eps = []

	for ep in entry_points.get_entry_points("console_scripts", path=fake_virtualenv):
		assert ep.group == "console_scripts"
		assert ep.distro is not None
		as_dict = ep._asdict()
		as_dict["extras"] = ep.extras
		as_dict["module"] = ep.module
		as_dict["attr"] = ep.attr
		as_dict["distro"] = as_dict["distro"]._asdict()
		as_dict["distro"]["path"] = as_dict["distro"]["path"].relative_to(tmp_pathplus)
		all_eps.append(as_dict)

	advanced_data_regression.check(sorted(all_eps, key=itemgetter("name")))


def test_get_all_entry_points(
		fake_virtualenv: List[PathPlus],
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	all_eps: Dict[str, List[Dict]] = {}

	for group, eps in entry_points.get_all_entry_points(path=fake_virtualenv).items():
		all_eps[group] = []

		for ep in eps:
			assert ep.group == group
			assert ep.distro is not None
			as_dict = ep._asdict()
			as_dict["extras"] = ep.extras
			as_dict["module"] = ep.module
			as_dict["attr"] = ep.attr
			as_dict["distro"] = as_dict["distro"]._asdict()
			as_dict["distro"]["path"] = as_dict["distro"]["path"].relative_to(tmp_pathplus)
			all_eps[group].append(as_dict)

		all_eps[group] = sorted(all_eps[group], key=itemgetter("name"))

	advanced_data_regression.check(all_eps)
