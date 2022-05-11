# stdlib
import inspect
import tempfile
from email.parser import HeaderParser
from operator import itemgetter
from typing import List, Set

# 3rd party
import handy_archives
import pytest
from apeye.requests_url import RequestsURL
from domdf_python_tools.paths import PathPlus
from first import first
from pypi_json import PyPIJSON

# this package
from dist_meta import metadata

top_packages: List[str] = [
		"urllib3",
		"botocore",
		"six",
		"boto3",
		"requests",
		"certifi",
		"idna",
		"chardet",
		"awscli",
		"s3transfer",
		"python-dateutil",
		"setuptools",
		"pyyaml",
		"pip",
		"numpy",
		"typing-extensions",
		"wheel",
		"cffi",
		"rsa",
		"pyasn1",
		"jmespath",
		"markupsafe",
		"pytz",
		"protobuf",
		"packaging",
		"jinja2",
		"importlib-metadata",
		"click",
		"pyparsing",
		"colorama",
		"zipp",
		"attrs",
		"oauthlib",
		"pandas",
		"pycparser",
		"requests-oauthlib",
		"docutils",
		"cryptography",
		"pyjwt",
		"google-api-core",
		"google-auth",
		"cachetools",
		"toml",
		"decorator",
		"pyasn1-modules",
		"isodate",
		"websocket-client",
		"pillow",
		"msrest",
		"future",
		"scipy",
		"werkzeug",
		"wrapt",
		"flask",
		"google-cloud-core",
		"lxml",
		"py",
		"google-cloud-storage",
		"azure-storage-blob",
		"sqlalchemy",
		"googleapis-common-protos",
		"azure-core",
		"tqdm",
		"docker",
		"grpcio",
		"pytest",
		"jsonschema",
		"pyrsistent",
		"itsdangerous",
		"appdirs",
		"pyarrow",
		"joblib",
		"multidict",
		"aiohttp",
		"yarl",
		"google-api-python-client",
		"scikit-learn",
		"pluggy",
		"psutil",
		"pygments",
		"matplotlib",
		"filelock",
		"google-resumable-media",
		"async-timeout",
		"regex",
		"azure-common",
		"httplib2",
		"pyopenssl",
		"greenlet",
		"mccabe",
		"uritemplate",
		"tabulate",
		"defusedxml",
		"prometheus-client",
		"virtualenv",
		"soupsieve",
		"coverage",
		"google-auth-httplib2",
		"typed-ast",
		"fsspec"
		]

cache_dir = PathPlus(tempfile.gettempdir()) / "wheel-cache"
cache_dir.maybe_make(parents=True)


@pytest.mark.flaky(reruns=1, reruns_delay=30)
@pytest.mark.parametrize("package", top_packages)
def test_loads(package: str):

	with PyPIJSON() as client:
		meta = client.get_metadata(package)

	latest_version = meta.info["version"]
	for release_artifact in filter(
			lambda x: x.endswith(".whl"), map(itemgetter("url"), meta.releases[latest_version])
			):

		release_url = RequestsURL(release_artifact)
		print(f"Checking {release_url.name}")

		wheel_filename = cache_dir / release_url.name

		if not wheel_filename.is_file():
			wheel_filename.write_bytes(release_url.get().content)
			assert wheel_filename.is_file()

		release_url.session.close()

		with handy_archives.ZipFile(wheel_filename, 'r') as wheel_zip:
			metadata_filename = first(wheel_zip.namelist(), key=lambda x: x.endswith(".dist-info/METADATA"))
			assert metadata_filename is not None
			metadata_file_content = wheel_zip.read_text(metadata_filename).replace("\r\n", '\n')

			stdlib_parser = HeaderParser().parsestr(metadata_file_content)
			dist_meta_parser = metadata.loads(metadata_file_content)

			if "Description" not in stdlib_parser:
				body = stdlib_parser.get_payload()
				if body:
					stdlib_parser["Description"] = body.strip() + '\n'
			else:
				stdlib_parser.replace_header(
						"Description", inspect.cleandoc(stdlib_parser["Description"]).rstrip() + '\n'
						)

			parsed_with_stdlib = sorted(stdlib_parser.items(), key=itemgetter(0))
			parsed_with_dist_meta = sorted(dist_meta_parser.items(), key=itemgetter(0))

			# Check keys
			assert list(map(itemgetter(0), parsed_with_stdlib)) == list(map(itemgetter(0), parsed_with_dist_meta))

			# Check values
			for stdlib_field, dist_meta_field in zip(parsed_with_stdlib, parsed_with_dist_meta):
				assert stdlib_field[0] == dist_meta_field[0]
				assert stdlib_field[1] == dist_meta_field[1]


@pytest.mark.parametrize("package", top_packages)
def test_loads_sdist(package: str):

	with PyPIJSON() as client:
		meta = client.get_metadata(package)

	latest_version = meta.info["version"]
	for release_artifact in filter(
			lambda x: x.endswith(".tar.gz"),
			map(itemgetter("url"), meta.releases[latest_version]),
			):

		release_url = RequestsURL(release_artifact)
		print(f"Checking {release_url.name}")

		wheel_filename = cache_dir / release_url.name

		if not wheel_filename.is_file():
			wheel_filename.write_bytes(release_url.get().content)
			assert wheel_filename.is_file()

		release_url.session.close()

		with handy_archives.TarFile.open(wheel_filename) as sdist_tar:
			metadata_filename = first(sdist_tar.getnames(), key=lambda x: x.endswith("PKG-INFO"))
			assert metadata_filename is not None
			metadata_file_content = sdist_tar.read_text(metadata_filename).replace("\r\n", '\n')

			stdlib_parser = HeaderParser().parsestr(metadata_file_content)
			dist_meta_parser = metadata.loads(metadata_file_content)

			if "Description" not in stdlib_parser:
				body = stdlib_parser.get_payload()
				if body:
					stdlib_parser["Description"] = body.strip() + '\n'
			else:
				stdlib_parser.replace_header(
						"Description", inspect.cleandoc(stdlib_parser["Description"]).rstrip() + '\n'
						)

			parsed_with_stdlib = sorted(stdlib_parser.items(), key=itemgetter(0))
			parsed_with_dist_meta = sorted(dist_meta_parser.items(), key=itemgetter(0))

			# Check keys
			assert list(map(itemgetter(0), parsed_with_stdlib)) == list(map(itemgetter(0), parsed_with_dist_meta))

			# Check values
			for stdlib_field, dist_meta_field in zip(parsed_with_stdlib, parsed_with_dist_meta):
				assert stdlib_field[0] == dist_meta_field[0]
				assert stdlib_field[1] == dist_meta_field[1]
