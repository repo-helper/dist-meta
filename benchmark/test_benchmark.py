# stdlib
from email.parser import HeaderParser

# 3rd party
import importlib_metadata
import pytest
from entrypoints import get_group_all, iter_files_distros
from importlib_metadata import entry_points, metadata, version

# this package
import dist_meta.metadata
from dist_meta.distributions import get_distribution
from dist_meta.entry_points import get_entry_points


class TestEntryPoints:

	@pytest.mark.benchmark(group="entry_points")
	def test_importlib_metadata(self, benchmark):

		def run():
			for group in ["console_scripts", "pytest11"]:
				for ep in entry_points().select(group=group):
					str(ep)

		benchmark(run)

	@pytest.mark.benchmark(group="entry_points")
	def test_entrypoints(self, benchmark):

		def run():
			for group in ["console_scripts", "pytest11"]:
				for ep in get_group_all(group):
					str(ep)

		benchmark(run)

	@pytest.mark.benchmark(group="entry_points")
	def test_dist_meta(self, benchmark):

		def run():
			for group in ["console_scripts", "pytest11"]:
				for ep in get_entry_points(group):
					str(ep)

		benchmark(run)


class TestDistribution:

	@pytest.mark.benchmark(group="distribution")
	def test_importlib_metadata(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(importlib_metadata.distribution(distro))

		benchmark(run)

	@pytest.mark.benchmark(group="distribution")
	def test_entrypoints(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				for cp, d in iter_files_distros():
					if d.name == distro:
						str(d)

		benchmark(run)

	@pytest.mark.benchmark(group="distribution")
	def test_dist_meta(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(get_distribution(distro))

		benchmark(run)


class TestMetadata:

	@pytest.mark.benchmark(group="metadata")
	def test_importlib_metadata(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(metadata(distro).keys())

		benchmark(run)

	@pytest.mark.benchmark(group="metadata")
	def test_dist_meta(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(get_distribution(distro).get_metadata().keys())

		benchmark(run)


class TestVersion:

	@pytest.mark.benchmark(group="version")
	def test_importlib_metadata(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(version(distro))

		benchmark(run)

	@pytest.mark.benchmark(group="version")
	def test_dist_meta(self, benchmark):

		def run():
			for distro in ["domdf-python-tools", "Sphinx", "wheel", "pYtEsT"]:
				str(get_distribution(distro).version)

		benchmark(run)


wheel_metadata_string = get_distribution("wheel").read_file("METADATA")
domdf_python_tools_metadata_string = get_distribution("domdf-python-tools").read_file("METADATA")
sphinx_metadata_string = get_distribution("Sphinx").read_file("METADATA")
pytest_metadata_string = get_distribution("pytest").read_file("METADATA")


class TestEmail:

	@pytest.mark.benchmark(group="email")
	def test_email(self, benchmark):

		def run():
			str(HeaderParser().parsestr(wheel_metadata_string))
			str(HeaderParser().parsestr(domdf_python_tools_metadata_string))
			str(HeaderParser().parsestr(sphinx_metadata_string))
			str(HeaderParser().parsestr(pytest_metadata_string))

		benchmark(run)

	@pytest.mark.benchmark(group="email")
	def test_dist_meta(self, benchmark):

		def run():
			str(dist_meta.metadata.loads(wheel_metadata_string))
			str(dist_meta.metadata.loads(domdf_python_tools_metadata_string))
			str(dist_meta.metadata.loads(sphinx_metadata_string))
			str(dist_meta.metadata.loads(pytest_metadata_string))

		benchmark(run)
