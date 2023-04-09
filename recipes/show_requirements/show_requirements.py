# stdlib
import re
import shutil
from typing import Iterable, List, Union

# 3rd party
import click
from consolekit import click_command
from consolekit.options import auto_default_option, flag_option, no_pager_option
from domdf_python_tools.iterative import make_tree
from domdf_python_tools.stringlist import StringList
from packaging.requirements import Requirement
from shippinglabel.requirements import ComparableRequirement, combine_requirements, list_requirements

# this package
import dist_meta.distributions


@no_pager_option()
@auto_default_option(
		"-d",
		"--depth",
		type=click.INT,
		help="The maximum depth to display. -1 means infinite depth.",
		show_default=True,
		)
@flag_option("-c", "--concise", help="Show a consolidated list of all dependencies.")
@click.argument("name", type=str)
@click_command()
def main(
		name: str,
		no_pager: bool = False,
		depth: int = -1,
		concise: bool = False,
		):
	"""
	Lists the requirements ``name``, and their dependencies.
	"""

	dist = dist_meta.distributions.get_distribution(name)

	buf = StringList([f"{dist.name}=={dist.version}"])
	raw_requirements = sorted(dist.get_metadata().get_all("Requires-Dist"))
	tree: List[Union[str, List[str], List[Union[str, List]]]] = []

	if concise:
		concise_requirements = []

		def flatten(iterable: Iterable[Union[Requirement, Iterable]]):
			for item in iterable:
				if isinstance(item, str):
					yield item
				else:
					yield from flatten(item)  # type: ignore[arg-type]

		for requirement in raw_requirements:
			concise_requirements.append(requirement)
			# TODO: remove "extra == " marker
			for req in flatten(list_requirements(str(requirement), depth=depth - 1)):
				concise_requirements.append(ComparableRequirement(re.sub('; extra == ".*"', '', req)))

		concise_requirements = sorted(set(combine_requirements(concise_requirements)))
		tree = list(map(str, concise_requirements))

	else:
		for requirement in raw_requirements:
			tree.append(str(requirement))
			deps = list(list_requirements(str(requirement), depth=depth - 1))
			if deps:
				tree.append(deps)

	buf.extend(make_tree(tree))

	if shutil.get_terminal_size().lines >= len(buf):
		# Don't use pager if fewer lines that terminal height
		no_pager = True

	if no_pager:
		click.echo(str(buf))
	else:
		click.echo_via_pager(str(buf))


if __name__ == "__main__":
	main()
