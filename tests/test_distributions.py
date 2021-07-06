# stdlib
import shutil
import zipfile
from operator import itemgetter
from typing import List, Optional

# 3rd party
import handy_archives
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from first import first
from packaging.utils import InvalidWheelFilename
from packaging.version import Version

# this package
from dist_meta import distributions

if "wheel" not in shutil._UNPACK_FORMATS:  # type: ignore
	shutil.register_unpack_format(
			name="wheel",
			extensions=[".whl"],
			function=shutil._unpack_zipfile,  # type: ignore
			)


def test_distribution(
		example_wheel,
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "site-packages").mkdir()
	shutil.unpack_archive(example_wheel, tmp_pathplus / "site-packages")

	filename: Optional[PathPlus] = first((tmp_pathplus / "site-packages").glob("*.dist-info"))
	assert filename is not None

	distro = distributions.Distribution.from_path(filename)

	advanced_data_regression.check({
			"filename": PathPlus(example_wheel).name,
			"name": distro.name,
			"version": str(distro.version),
			"path": distro.path.name,
			"wheel": list(distro.get_wheel().items()),  # type: ignore
			"metadata": list(distro.get_metadata().items()),
			"entry_points": distro.get_entry_points(),
			"has_license": distro.has_file("LICENSE"),
			"top_level": distro.read_file("top_level.txt"),
			"repr": repr(distro),
			})

	(filename / "WHEEL").unlink()
	assert distro.get_wheel() is None


def test_wheel_distribution(
		example_wheel,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	wd = distributions.WheelDistribution.from_path(example_wheel)

	advanced_data_regression.check({
			"filename": PathPlus(example_wheel).name,
			"name": wd.name,
			"version": str(wd.version),
			"path": wd.path.name,
			"wheel": list(wd.get_wheel().items()),
			"metadata": list(wd.get_metadata().items()),
			"entry_points": wd.get_entry_points(),
			"has_license": wd.has_file("LICENSE"),
			"top_level": wd.read_file("top_level.txt"),
			"repr": repr(wd),
			})

	assert isinstance(wd.wheel_zip, zipfile.ZipFile)
	assert isinstance(wd.wheel_zip, handy_archives.ZipFile)


def test_wheel_distribution_zip(
		wheel_directory,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	wd = distributions.WheelDistribution.from_path(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl")

	assert isinstance(wd.wheel_zip, zipfile.ZipFile)
	assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

	advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

	with wd:
		advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

	assert wd.wheel_zip.fp is None


def test_iter_distributions(
		fake_virtualenv: List[PathPlus],
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	all_dists = []

	for dist in distributions.iter_distributions(path=fake_virtualenv):
		assert dist.path.is_dir()
		assert dist.has_file("METADATA")
		assert dist.has_file("WHEEL")
		as_dict = dist._asdict()
		as_dict["path"] = as_dict["path"].relative_to(tmp_pathplus)
		all_dists.append(as_dict)

	advanced_data_regression.check(sorted(all_dists, key=itemgetter("name")))


@pytest.mark.parametrize(
		"name, expected",
		[
				("Babel", "Babel"),
				("babel", "Babel"),
				("BaBeL", "Babel"),
				("sphinxcontrib_applehelp", "sphinxcontrib_applehelp"),
				("sphinxcontrib-applehelp", "sphinxcontrib_applehelp"),
				("sphinxcontrib.applehelp", "sphinxcontrib_applehelp"),
				]
		)
def test_get_distribution(name, expected, fake_virtualenv: List[PathPlus]):
	assert distributions.get_distribution(name, path=fake_virtualenv).name == expected


def test_get_distribution_shadowing(fake_virtualenv: List[PathPlus]):
	distro = distributions.get_distribution("domdf_python_tools", path=fake_virtualenv)
	assert distro.name == "domdf_python_tools"
	assert distro.version == Version("2.2.0")

	distro = distributions.get_distribution("domdf-python-tools", path=fake_virtualenv)
	assert distro.name == "domdf_python_tools"
	assert distro.version == Version("2.2.0")


def test_get_distribution_not_found(fake_virtualenv: List[PathPlus]):
	with pytest.raises(distributions.DistributionNotFoundError, match="sphinxcontrib_jsmath"):
		distributions.get_distribution("sphinxcontrib_jsmath", path=fake_virtualenv)


def test_parse_wheel_filename_errors():
	with pytest.raises(InvalidWheelFilename, match=r"Invalid wheel filename \(extension must be '.whl'\): .*"):
		distributions._parse_wheel_filename(PathPlus("my_project-0.1.2.tar.gz"))

	with pytest.raises(InvalidWheelFilename, match=r"Invalid wheel filename \(wrong number of parts\): .*"):
		distributions._parse_wheel_filename(PathPlus("dist_meta-0.0.0-py2-py3-py4-none-any.whl"))

	with pytest.raises(InvalidWheelFilename, match="Invalid project name: 'dist__meta'"):
		distributions._parse_wheel_filename(PathPlus("dist__meta-0.0.0-py3-none-any.whl"))

	with pytest.raises(InvalidWheelFilename, match=r"Invalid project name: '\?\?\?'"):
		distributions._parse_wheel_filename(PathPlus("???-0.0.0-py3-none-any.whl"))
