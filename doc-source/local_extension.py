# From https://github.com/pradyunsg/sphinx-inline-tabs
# Copyright (c) 2020 Pradyun Gedam <mail@pradyunsg.me>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

# stdlib
import shutil
from typing import Optional

# 3rd party
import sphinx_inline_tabs
from docutils import nodes
from domdf_python_tools.paths import PathPlus
from sphinx.application import Sphinx
from sphinx.errors import NoUri
from sphinx_inline_tabs._impl import TabDirective, TabHtmlTransform, _TabInput, _TabLabel


def copy_asset_files(app: Sphinx, exception: Optional[Exception] = None) -> None:
	"""
	Copy asset files to the output.

	:param app: The Sphinx application.
	:param exception: Any exception which occurred and caused Sphinx to abort.
	"""

	if exception:  # pragma: no cover
		return

	if app.builder.format.lower() != "html":
		return

	source_dir = PathPlus(sphinx_inline_tabs.__file__).parent / "static"

	css_static_dir = PathPlus(app.builder.outdir) / "_static" / "css"
	css_static_dir.maybe_make(parents=True)
	shutil.copy2(source_dir / "tabs.css", css_static_dir / "inline-tabs.css")

	js_static_dir = PathPlus(app.builder.outdir) / "_static" / "js"
	js_static_dir.maybe_make(parents=True)
	shutil.copy2(source_dir / "tabs.js", js_static_dir / "inline-tabs.js")


def handle_missing_xref(app: Sphinx, env, node: nodes.Node, contnode: nodes.Node) -> None:
	# Ignore missing reference warnings for the wheel_filename module
	if node.get("reftarget", '') == "dist_meta.metadata_mapping._T":
		raise NoUri


def setup(app: Sphinx):
	# We do imports from Sphinx, after validating the Sphinx version

	app.add_directive("inline-tab", TabDirective)
	app.add_post_transform(TabHtmlTransform)
	app.add_node(_TabInput, html=(_TabInput.visit, _TabInput.depart))
	app.add_node(_TabLabel, html=(_TabLabel.visit, _TabLabel.depart))

	# Include our static assets
	app.connect("build-finished", copy_asset_files)
	app.add_js_file("js/inline-tabs.js")
	app.add_css_file("css/inline-tabs.css")

	app.connect("missing-reference", handle_missing_xref, priority=950)

	return {
			"parallel_read_safe": True,
			"parallel_write_safe": True,
			}
