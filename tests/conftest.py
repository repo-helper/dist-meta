# stdlib
from typing import List

# 3rd party
import handy_archives
import pytest
from domdf_python_tools.paths import PathPlus

pytest_plugins = ("coincidence", "tests.yaml_packaging")

_original_wheel_directory = PathPlus(__file__).parent / "wheels"


@pytest.fixture(scope="session")
def wheel_directory() -> PathPlus:
	return _original_wheel_directory


@pytest.fixture()
def fake_virtualenv(
		wheel_directory,
		tmp_pathplus: PathPlus,
		) -> List[PathPlus]:

	site_packages = (tmp_pathplus / "python3.8" / "site-packages")
	dist_packages = (tmp_pathplus / "dist-packages")

	site_packages.mkdir(parents=True)
	dist_packages.mkdir()

	for filename in [
			"Babel-2.9.1-py2.py3-none-any.whl",
			"certifi-2021.5.30-py2.py3-none-any.whl",
			"appdirs-1.4.4-py2.py3-none-any.whl",
			"alabaster-0.7.12-py2.py3-none-any.whl",
			"apeye-1.0.1-py3-none-any.whl",
			"importlib_metadata-4.5.0-py3-none-any.whl",
			"Sphinx-3.5.4-py3-none-any.whl",
			"cawdrey-0.4.2-py3-none-any.whl",
			"sphinxcontrib_applehelp-1.0.2-py2.py3-none-any.whl",
			"packaging-20.9-py2.py3-none-any.whl",
			"Jinja2-3.0.1-py3-none-any.whl",
			"dom_toml-0.5.0-py3-none-any.whl",
			"wheel_filename-1.3.0-py3-none-any.whl",
			"typing_extensions-3.10.0.0-py3-none-any.whl",
			"domdf_python_tools-2.2.0-py3-none-any.whl",
			"PyAthena-2.3.0-py3-none-any.whl",
			"buildbot_gitea-1.7.0-py3-none-any.whl",
			]:

		handy_archives.unpack_archive(str(wheel_directory / filename), site_packages)

	handy_archives.unpack_archive(wheel_directory / "domdf_python_tools-2.9.1-py3-none-any.whl", dist_packages)
	(site_packages / "_virtualenv.py").touch()
	(site_packages / "_virtualenv.pth").touch()
	(site_packages / "distutils-precedence.pth").touch()

	(tmp_pathplus / "wheel-0.36.2-py3.8.egg").touch()

	return [site_packages, dist_packages, tmp_pathplus / "wheel-0.36.2-py3.8.egg"]
