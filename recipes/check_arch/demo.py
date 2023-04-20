# stdlib
import io
import zipfile

# 3rd party
import httpx
from domdf_python_tools.paths import PathPlus
from packaging.tags import parse_tag, platform_tags

# this package
from dist_meta.distributions import iter_distributions

fake_venv = PathPlus("fake-venv/lib/python3.8/site-packages")
fake_venv.maybe_make(parents=True)

if True:

	for artifact in [
			"https://files.pythonhosted.org/packages/92/06/41460a239909eb07023bc7ea18fbd0dcdb4e1ec4527b465d1e5b56380514/regex-2022.3.15-cp310-cp310-macosx_10_9_x86_64.whl",
			"https://files.pythonhosted.org/packages/df/06/c515c5bc43b90462e753bc768e6798193c6520c9c7eb2054c7466779a9db/MarkupSafe-2.1.1-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
			]:
		r = httpx.get(artifact)
		z = zipfile.ZipFile(io.BytesIO(r.content))
		z.extractall(fake_venv)

supported_tags = set(platform_tags())
supported_tags.add("any")

# fake_venv = "venv/lib/python3.8/site-packages/"

# 3rd party
from check_arch import check

check([fake_venv])
