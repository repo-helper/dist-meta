# stdlib
import os
import platform
import shutil
import sys
import zipfile
from operator import itemgetter
from typing import List, Optional, Tuple

# 3rd party
import handy_archives
import pytest
from coincidence import min_version
from coincidence.params import param
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from coincidence.selectors import not_pypy, only_pypy, only_version
from domdf_python_tools.compat import PYPY36
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from first import first
from packaging.utils import InvalidWheelFilename
from packaging.version import Version
from shippinglabel.checksum import get_sha256_hash

# this package
from dist_meta import _utils, distributions

_wheels_glob = (PathPlus(__file__).parent / "wheels").glob("*.whl")


@pytest.fixture(params=(param(w, key=lambda t: t[0].name) for w in _wheels_glob))
def example_wheel(tmp_pathplus: PathPlus, request) -> PathPlus:
	return shutil.copy2(request.param, tmp_pathplus)


def _name_param(params):  # noqa: MAN001,MAN002
	wheel = params[0]
	if wheel.name == "PyAthena-2.3.0-py3-none-any.whl":
		# PyAthena has a CamelCase filename but lowercase metadata
		return "PyAthena-2.3.0-py3-none-any.whl_Distribution"

	return wheel.name


class TestDistribution:

	@pytest.mark.parametrize(
			"example_wheel",
			[param(w, key=_name_param) for w in (PathPlus(__file__).parent / "wheels").glob("*.whl")],
			)
	def test_distribution(
			self,
			example_wheel: PathPlus,
			tmp_pathplus: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):

		if PYPY36 and platform.system() == "Windows":
			pytest.skip("Fails due to internal error on PyPy 3.6 on Windows")

		(tmp_pathplus / "site-packages").mkdir()
		handy_archives.unpack_archive(example_wheel, tmp_pathplus / "site-packages")

		filename: Optional[PathPlus] = first((tmp_pathplus / "site-packages").glob("*.dist-info"))
		assert filename is not None

		distro = distributions.Distribution.from_path(filename)

		wheel = distro.get_wheel()
		assert wheel is not None

		advanced_data_regression.check({
				"filename": PathPlus(example_wheel).name,
				"name": distro.name,
				"version": str(distro.version),
				"wheel": list(wheel.items()),
				"metadata": list(distro.get_metadata().items()),
				"entry_points": distro.get_entry_points(),
				"has_license": distro.has_file("LICENSE"),
				})

		advanced_file_regression.check(repr(distro), extension="_distro.repr")
		advanced_file_regression.check(distro.path.name, extension="_distro.path")

		assert distro.get_record()

		(filename / "WHEEL").unlink()
		assert distro.get_wheel() is None
		assert distro.get_record()

		(filename / "RECORD").unlink()
		assert distro.get_record() is None

	def test_from_path_pip_tmpdir(self):
		msg = r"Directory path starts with a tilde \(~\). This may be a temporary directory created by pip."

		with pytest.raises(ValueError, match=msg):
			distributions.Distribution.from_path("/some/directory/~-ippinglabel.1.1.1.post1.dist-info")

	def test_get_record(self, example_wheel: PathPlus, tmp_pathplus: PathPlus):
		(tmp_pathplus / "site-packages").mkdir()
		handy_archives.unpack_archive(example_wheel, tmp_pathplus / "site-packages")

		filename: Optional[PathPlus] = first((tmp_pathplus / "site-packages").glob("*.dist-info"))
		assert filename is not None

		distro = distributions.Distribution.from_path(filename)
		record = distro.get_record()
		assert record is not None
		assert len(record)  # pylint: disable=len-as-condition

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
	cls = distributions.WheelDistribution
	repr_filename = "_wd.repr"

	def test_distribution(
			self,
			example_wheel: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):
		wd = self.cls.from_path(example_wheel)

		advanced_data_regression.check({
				"filename": PathPlus(example_wheel).name,
				"name": wd.name,
				"version": str(wd.version),
				"wheel": list(wd.get_wheel().items()),
				"metadata": list(wd.get_metadata().items()),
				"entry_points": wd.get_entry_points(),
				"has_license": wd.has_file("LICENSE"),
				})

		advanced_file_regression.check(repr(wd), extension=self.repr_filename)
		advanced_file_regression.check(wd.path.name, extension="_wd.path")

		assert isinstance(wd.wheel_zip, zipfile.ZipFile)
		assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

	def test_get_record(self, example_wheel: PathPlus):

		distro = self.cls.from_path(example_wheel)
		record = distro.get_record()
		assert record is not None
		assert len(record)  # pylint: disable=len-as-condition

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
			self,
			wheel_directory: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			):
		wd = self.cls.from_path(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl")

		assert isinstance(wd.wheel_zip, zipfile.ZipFile)
		assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

		advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

		with wd:
			advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

		assert wd.wheel_zip.fp is None


class CustomDistribution(distributions.DistributionType, Tuple[str, Version, PathPlus, handy_archives.ZipFile]):

	@property
	def path(self) -> PathPlus:
		"""
		The path to the ``.whl`` file.
		"""

		return self[2]

	@property
	def wheel_zip(self) -> handy_archives.ZipFile:
		"""
		The opened zip file.
		"""

		return self[3]

	__slots__ = ()
	_fields = ("name", "version", "path", "wheel_zip")

	def __new__(
			cls,
			name: str,
			version: Version,
			path: PathPlus,
			wheel_zip: handy_archives.ZipFile,
			):
		return tuple.__new__(cls, (name, version, path, wheel_zip))

	@classmethod
	def from_path(cls, path: PathLike, **kwargs) -> "CustomDistribution":
		r"""
		Construct a :class:`~.WheelDistribution` from a filesystem path to the ``.whl`` file.

		:param path:
		:param \*\*kwargs: Additional keyword arguments passed to :class:`zipfile.ZipFile`.
		"""

		path = PathPlus(path)
		name, version, *_ = _utils._parse_wheel_filename(path)
		wheel_zip = handy_archives.ZipFile(path, 'r', **kwargs)

		return cls(name, version, path, wheel_zip)

	read_file = distributions.WheelDistribution.read_file
	has_file = distributions.WheelDistribution.has_file


class CustomSubclass(distributions.WheelDistribution):

	extra_attribute: str

	@property
	def url(self) -> str:
		"""
		The URL of the remote wheel.
		"""

		return "https://foo.bar/wheel.whl"

	__slots__ = ()
	_fields = ("name", "version", "path", "wheel_zip")

	def __new__(
			cls,
			name: str,
			version: Version,
			path: PathPlus,
			wheel_zip: handy_archives.ZipFile,
			):
		self = super().__new__(cls, name, version, path, wheel_zip)
		self.extra_attribute = "EXTRA"
		return self

	def extra_method(self):  # noqa: MAN002
		raise NotImplementedError("extra_method")


class TestCustomDistribution:

	def test_distribution(
			self,
			example_wheel: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):
		wd = CustomDistribution.from_path(example_wheel)

		wheel = wd.get_wheel()
		assert wheel is not None

		advanced_data_regression.check({
				"filename": PathPlus(example_wheel).name,
				"name": wd.name,
				"version": str(wd.version),
				"wheel": list(wheel.items()),
				"metadata": list(wd.get_metadata().items()),
				"entry_points": wd.get_entry_points(),
				"has_license": wd.has_file("LICENSE"),  # type: ignore[misc]
				})

		advanced_file_regression.check(repr(wd), extension="_cd.repr")
		advanced_file_regression.check(wd.path.name, extension="_wd.path")

		assert isinstance(wd.wheel_zip, zipfile.ZipFile)
		assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

	def test_get_record(self, example_wheel: PathPlus):

		distro = CustomDistribution.from_path(example_wheel)
		record = distro.get_record()
		assert record is not None
		assert len(record)  # pylint: disable=len-as-condition

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

	def test_namedtuple_methods(self):
		dist = CustomDistribution(
				"demo",
				Version("1.2.3"),
				PathPlus("foo/bar/baz.whl"),
				None,  # type: ignore[arg-type]
				)
		assert dist._asdict() == {
				"name": "demo",
				"version": Version("1.2.3"),
				"path": PathPlus("foo/bar/baz.whl"),
				"wheel_zip": None,
				}
		assert dist.__getnewargs__() == (
				"demo",
				Version("1.2.3"),
				PathPlus("foo/bar/baz.whl"),
				None,
				)
		assert dist._replace(name="replaced").name == "replaced"
		assert dist._replace(name="replaced").version == Version("1.2.3")

		assert dist._replace(version=Version("4.5.6")).version == Version("4.5.6")
		assert dist._replace(version=Version("4.5.6")).name == "demo"

		with pytest.raises(ValueError, match=r"Got unexpected field names: \['foo', 'bar'\]"):
			dist._replace(foo="abc", bar=123)

		expected = CustomDistribution(
				"demo",
				Version("1.2.3"),
				PathPlus("foo/bar/baz.whl"),
				None,  # type: ignore[arg-type]
				)
		made = CustomDistribution._make((
				"demo",
				Version("1.2.3"),
				PathPlus("foo/bar/baz.whl"),
				None,
				))
		assert made == expected


class TestCustomSubclass(TestWheelDistribution):
	cls = CustomSubclass
	repr_filename = "_cs.repr"

	def test_wheel_distribution_zip(
			self,
			wheel_directory: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			):
		wd = CustomSubclass.from_path(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl")

		assert isinstance(wd.wheel_zip, zipfile.ZipFile)
		assert isinstance(wd.wheel_zip, handy_archives.ZipFile)

		advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

		with wd:
			advanced_file_regression.check(wd.wheel_zip.read("domdf_python_tools/__init__.py").decode("UTF-8"))

		assert wd.wheel_zip.fp is None

	def test_subclass(self, wheel_directory: PathPlus):
		wd = CustomSubclass.from_path(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl")

		wd2 = distributions.WheelDistribution.from_path(
				wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl"
				)

		assert wd[:2] == wd2[:2]
		# assert wd == wd2  # wheel_zip breaks equality
		assert isinstance(wd, CustomSubclass)
		assert isinstance(wd, distributions.WheelDistribution)
		assert isinstance(wd, distributions.DistributionType)

		assert wd.url == "https://foo.bar/wheel.whl"
		assert wd.extra_attribute == "EXTRA"

		with pytest.raises(NotImplementedError, match="extra_method"):
			wd.extra_method()


def test_iter_distributions(
		fake_virtualenv: List[PathPlus],
		tmp_pathplus: PathPlus,
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


def test_iter_distributions_pip_tmpdir(
		fake_virtualenv: List[PathPlus],
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	site_packages = fake_virtualenv[0]
	shutil.move(
			os.fspath(site_packages / "alabaster-0.7.12.dist-info"),
			site_packages / "~-abaster-0.7.12.dist-info",
			)

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
def test_get_distribution(name: str, expected: str, fake_virtualenv: List[PathPlus]):
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
		_utils._parse_wheel_filename(PathPlus("my_project-0.1.2.tar.gz"))

	with pytest.raises(InvalidWheelFilename, match=r"Invalid wheel filename \(wrong number of parts\): .*"):
		_utils._parse_wheel_filename(PathPlus("dist_meta-0.0.0-py2-py3-py4-none-any.whl"))

	with pytest.raises(InvalidWheelFilename, match="Invalid project name: 'dist__meta'"):
		_utils._parse_wheel_filename(PathPlus("dist__meta-0.0.0-py3-none-any.whl"))

	with pytest.raises(InvalidWheelFilename, match=r"Invalid project name: '\?\?\?'"):
		_utils._parse_wheel_filename(PathPlus("???-0.0.0-py3-none-any.whl"))


@min_version(3.7, reason="hpy on PyPy requires Python 3.7 or greater.")
def test_hpy_pypy():
	pytest.importorskip("hpy")

	distro = distributions.get_distribution("hpy")
	assert distro.name == "hpy"

	if sys.implementation.name == "pypy":
		assert distro.version == Version("0.0.0")
	else:
		assert distro.version == Version("0.0.3")


@min_version(3.7)
def test_cffi_pypy():
	pytest.importorskip("cffi")

	distro = distributions.get_distribution("cffi")
	assert distro.name == "cffi"

	if sys.implementation.name == "pypy":
		assert distro.version == Version("0.0.0")
	# else:
	# 	assert distro.version == Version("0.0.3")


def test_abc_bad_subclass():

	with pytest.raises(ValueError, match="'_fields' cannot be empty."):

		class BadSubclass1(distributions.DistributionType):
			_fields = ()

	with pytest.raises(ValueError, match="The first item in '_fields' must be 'name'"):

		class BadSubclass2(distributions.DistributionType):
			_fields = ("version", "name")

	with pytest.raises(ValueError, match="The second item in '_fields' must be 'version'"):

		class BadSubclass3(distributions.DistributionType):
			_fields = ("name", "build_number")


def test_wheel_no_dist_info(tmp_pathplus: PathPlus):
	with in_directory(tmp_pathplus):
		handy_archives.ZipFile("foo-1.2.3-py3-none-any.whl", 'w').close()

	wd = distributions.WheelDistribution.from_path(tmp_pathplus / "foo-1.2.3-py3-none-any.whl")
	assert wd.name == "foo"
	assert wd.version == Version("1.2.3")

	with pytest.raises(FileNotFoundError, match="^foo-1.2.3.dist-info/WHEEL$"):
		wd.get_wheel()

	assert not wd.has_file("WHEEL")


def test_wheel_no_quite_dist_info(tmp_pathplus: PathPlus):
	with in_directory(tmp_pathplus):
		with handy_archives.ZipFile("foo-1.2.3-py3-none-any.whl", 'w') as fake_wheel:
			fake_wheel.writestr("foo-1.2.3.dist-information", '')

	wd = distributions.WheelDistribution.from_path(tmp_pathplus / "foo-1.2.3-py3-none-any.whl")
	assert wd.name == "foo"
	assert wd.version == Version("1.2.3")

	with pytest.raises(FileNotFoundError, match="^foo-1.2.3.dist-info/WHEEL$"):
		wd.get_wheel()

	assert not wd.has_file("WHEEL")


def test_wheel_wrong_dist_info(tmp_pathplus: PathPlus):
	with in_directory(tmp_pathplus):
		with handy_archives.ZipFile("foo-1.2.3-py3-none-any.whl", 'w') as fake_wheel:
			fake_wheel.writestr("bar-4.5.6.dist-info/WHEEL", '')

	wd = distributions.WheelDistribution.from_path(tmp_pathplus / "foo-1.2.3-py3-none-any.whl")
	assert wd.name == "foo"
	assert wd.version == Version("1.2.3")

	with pytest.raises(FileNotFoundError, match="^foo-1.2.3.dist-info/WHEEL$"):
		wd.get_wheel()

	assert not wd.has_file("WHEEL")


@pytest.mark.parametrize(
		"version",
		[
				pytest.param(
						"3.6",
						marks=[
								only_version(3.6, reason="Output differs on Python 3.6"),
								not_pypy("Output differs on PyPy")
								]
						),
				pytest.param(
						"3.6-pypy",
						marks=[
								only_version(3.6, reason="Output differs on Python 3.6"),
								only_pypy("Output differs on PyPy")
								]
						),
				pytest.param(
						"cpython",
						marks=[
								pytest.mark.skipif(
										not ((3, 7) <= sys.version_info[:2] <= (3, 10)),
										reason="Output differs on Python 3.7"
										),
								not_pypy("Output differs on PyPy")
								]
						),
				pytest.param(
						"pypy",
						marks=[
								pytest.mark.skipif(
										not ((3, 7) <= sys.version_info[:2] <= (3, 10)),
										reason="Output differs on Python 3.7"
										),
								only_pypy("Output differs on PyPy")
								]
						),
				pytest.param("3.11", marks=only_version("3.11", reason="Output differs on Python 3.11")),
				]
		)
def test_packages_distributions(advanced_data_regression: AdvancedDataRegressionFixture, version):

	data = distributions.packages_distributions()
	advanced_data_regression.check({k: list(v) for k, v in data.items()})
