# stdlib
import os
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
from shippinglabel.checksum import get_sha256_hash

# this package
from dist_meta import distributions

if "wheel" not in shutil._UNPACK_FORMATS:  # type: ignore
	shutil.register_unpack_format(
			name="wheel",
			extensions=[".whl"],
			function=shutil._unpack_zipfile,  # type: ignore
			)


class TestDistribution:

	def test_distribution(
			self,
			example_wheel,
			tmp_pathplus: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):

		(tmp_pathplus / "site-packages").mkdir()
		handy_archives.unpack_archive(example_wheel, tmp_pathplus / "site-packages")

		filename: Optional[PathPlus] = first((tmp_pathplus / "site-packages").glob("*.dist-info"))
		assert filename is not None

		distro = distributions.Distribution.from_path(filename)

		advanced_data_regression.check({
				"filename": PathPlus(example_wheel).name,
				"name": distro.name,
				"version": str(distro.version),
				"wheel": list(distro.get_wheel().items()),  # type: ignore
				"metadata": list(distro.get_metadata().items()),
				"entry_points": distro.get_entry_points(),
				"has_license": distro.has_file("LICENSE"),
				"top_level": distro.read_file("top_level.txt"),
				})

		advanced_file_regression.check(repr(distro), extension="_distro.repr")
		advanced_file_regression.check(distro.path.name, extension="_distro.path")

		assert distro.get_record()

		(filename / "WHEEL").unlink()
		assert distro.get_wheel() is None
		assert distro.get_record()

		(filename / "RECORD").unlink()
		assert distro.get_record() is None

	def test_get_record(
			self,
			example_wheel,
			tmp_pathplus: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):

		(tmp_pathplus / "site-packages").mkdir()
		handy_archives.unpack_archive(example_wheel, tmp_pathplus / "site-packages")

		filename: Optional[PathPlus] = first((tmp_pathplus / "site-packages").glob("*.dist-info"))
		assert filename is not None

		distro = distributions.Distribution.from_path(filename)
		record = distro.get_record()
		assert record is not None
		assert len(record)

		for file in record:
			assert (distro.path.parent / file).exists()
			assert (distro.path.parent / file).is_file()

			if file.hash is None:
				assert file.name == "RECORD"
			else:
				assert get_sha256_hash(distro.path.parent / file).hexdigest() == file.hash.hexdigest()

			if file.size is not None:
				assert (distro.path.parent / file).stat().st_size == file.size

			assert file.distro is distro
			file.read_bytes()  # will fail if can't read


class TestWheelDistribution:

	def test_distribution(
			self,
			example_wheel,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):
		wd = distributions.WheelDistribution.from_path(example_wheel)

		advanced_data_regression.check({
				"filename": PathPlus(example_wheel).name,
				"name": wd.name,
				"version": str(wd.version),
				"wheel": list(wd.get_wheel().items()),
				"metadata": list(wd.get_metadata().items()),
				"entry_points": wd.get_entry_points(),
				"has_license": wd.has_file("LICENSE"),
				"top_level": wd.read_file("top_level.txt"),
				})

		advanced_file_regression.check(repr(wd), extension="_wd.repr")
		advanced_file_regression.check(wd.path.name, extension="_wd.path")

		assert isinstance(wd.wheel_zip, zipfile.ZipFile)
		assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

	def test_get_record(
			self,
			example_wheel,
			tmp_pathplus: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):

		distro = distributions.WheelDistribution.from_path(example_wheel)
		record = distro.get_record()
		assert record is not None
		assert len(record)

		for file in record:

			if file.hash is None:
				assert file.name == "RECORD"
			else:
				with distro.wheel_zip.open(os.fspath(file)) as fp:
					assert get_sha256_hash(fp).hexdigest() == file.hash.hexdigest()

			if file.size is not None:
				assert distro.wheel_zip.getinfo(os.fspath(file)).file_size == file.size

			assert file.distro is None

			with pytest.raises(ValueError, match="Cannot read files with 'self.distro = None'"):
				file.read_bytes()


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
