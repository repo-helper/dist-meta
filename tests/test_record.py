# 3rd party
import handy_archives
import pytest
from coincidence import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from shippinglabel.checksum import get_sha256_hash

# this package
from dist_meta.distributions import Distribution
from dist_meta.record import FileHash, RecordEntry


def test_file_hash(tmp_pathplus: PathPlus):

	(tmp_pathplus / "LICENSE").write_text("Do what you want,")

	fh = FileHash("sha256", "WUk2cO6oqWOYz3wqsKUFJi432cyMjFrMjiucuBR3K4E")
	assert fh.to_string() == "sha256=WUk2cO6oqWOYz3wqsKUFJi432cyMjFrMjiucuBR3K4E"
	assert FileHash.from_string("sha256=WUk2cO6oqWOYz3wqsKUFJi432cyMjFrMjiucuBR3K4E") == fh

	sha256_hash = get_sha256_hash(tmp_pathplus / "LICENSE")
	assert fh.hexdigest() == sha256_hash.hexdigest()
	assert fh.digest() == sha256_hash.digest()
	assert FileHash.from_hash(sha256_hash) == fh


def test_record_entry(
		wheel_directory: PathPlus,
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):

	handy_archives.unpack_archive(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl", tmp_pathplus)
	dist_info = tmp_pathplus / "domdf_python_tools-2.9.1.dist-info"
	assert dist_info.is_dir()

	license_file = dist_info / "LICENSE"
	assert license_file.is_file()

	distro = Distribution.from_path(dist_info)

	license_record = RecordEntry(
			license_file.relative_to(tmp_pathplus),
			FileHash("sha256", "46mU2C5kSwOnkqkw9XQAJlhBL2JAf1_uCD8lVcXyMRg"),
			7652,
			distro,
			)

	assert license_record.size == 7652
	assert license_record.hash is not None
	assert license_record.hash.to_string() == "sha256=46mU2C5kSwOnkqkw9XQAJlhBL2JAf1_uCD8lVcXyMRg"

	assert license_record.read_text() == license_file.read_text()
	assert license_record.read_bytes() == license_file.read_bytes()

	expected = "domdf_python_tools-2.9.1.dist-info/LICENSE,sha256=46mU2C5kSwOnkqkw9XQAJlhBL2JAf1_uCD8lVcXyMRg,7652"
	assert license_record.as_record_entry() == expected

	advanced_file_regression.check(repr(license_record))


def test_record_entry_no_distro(
		wheel_directory: PathPlus,
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	handy_archives.unpack_archive(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl", tmp_pathplus)
	dist_info = tmp_pathplus / "domdf_python_tools-2.9.1.dist-info"
	assert dist_info.is_dir()

	license_file = dist_info / "LICENSE"
	assert license_file.is_file()

	license_record = RecordEntry(
			license_file.relative_to(tmp_pathplus),
			FileHash("sha256", "46mU2C5kSwOnkqkw9XQAJlhBL2JAf1_uCD8lVcXyMRg"),
			7652,
			)

	with pytest.raises(ValueError, match="Cannot read files with 'self.distro = None'"):
		license_record.read_text()
	with pytest.raises(ValueError, match="Cannot read files with 'self.distro = None'"):
		license_record.read_bytes()

	expected = "domdf_python_tools-2.9.1.dist-info/LICENSE,sha256=46mU2C5kSwOnkqkw9XQAJlhBL2JAf1_uCD8lVcXyMRg,7652"
	assert license_record.as_record_entry() == expected

	advanced_file_regression.check(repr(license_record))


def test_record_entry_no_attributes(
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	license_record = RecordEntry("domdf_python_tools-2.9.1.dist-info/RECORD")

	with pytest.raises(ValueError, match="Cannot read files with 'self.distro = None'"):
		license_record.read_text()
	with pytest.raises(ValueError, match="Cannot read files with 'self.distro = None'"):
		license_record.read_bytes()

	assert license_record.as_record_entry() == "domdf_python_tools-2.9.1.dist-info/RECORD,,"

	advanced_file_regression.check(repr(license_record))


@pytest.mark.parametrize(
		"record_string",
		[
				pytest.param(
						"apeye-1.0.1.dist-info/INSTALLER,sha256=zuuue4knoyJ-UwPPXg8fezS7VCrXJQrAP7zeNuwvFQg,4",
						id="INSTALLER"
						),
				pytest.param("apeye/__pycache__/email_validator.cpython-38.pyc,,", id="__pycache__"),
				pytest.param(
						"apeye/cache.py,sha256=NIQAPrl-YG2wYo-xomLJhy9Iyq9NM6hMSeYoxJBtI28,4158", id="cache.py"
						),
				pytest.param(
						"apeye/public_suffix_list.dat,sha256=sIQS28R2dRmXsqHy1dLS2poPCw9luJPejevcHnhvCME,233455",
						id="public_suffix_list.dat"
						),
				pytest.param("apeye/py.typed,sha256=47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU,0", id="py.typed"),
				]
		)
def test_from_record_entry_string(record_string: str, advanced_data_regression: AdvancedDataRegressionFixture):
	record = RecordEntry.from_record_entry(record_string)
	assert record.as_record_entry() == record_string
	advanced_data_regression.check({"path": record, "size": record.size, "hash": record.hash})

	fake_distro = object()
	record = RecordEntry.from_record_entry(record_string, distro=fake_distro)  # type: ignore
	assert record.as_record_entry() == record_string
	assert record.distro is fake_distro
