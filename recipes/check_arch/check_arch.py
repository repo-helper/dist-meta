"""
Check installed wheels have the correct architecture.
"""

# stdlib
import sys
from typing import Tuple

# 3rd party
from consolekit import click_command, option
from consolekit.options import flag_option
from domdf_python_tools.words import Plural, PluralPhrase, word_join
from natsort import natsorted
from packaging.tags import parse_tag, platform_tags

# this package
from dist_meta.distributions import iter_distributions

supported_tags = set(platform_tags())
supported_tags.add("any")
# supported_tags = set()

_supported_platforms = PluralPhrase(
		"The {} it supports {}",
		(Plural("platform", "platforms"), Plural("is", "are")),
		)


def print_tags(ctx, param, tags: bool = False):
	if not tags or ctx.resilient_parsing:
		return
	print('\n'.join(natsorted(supported_tags)))
	ctx.exit()


def check(path: Tuple[str, ...]) -> int:
	ret = 0

	for dist in iter_distributions(path):
		wheel_file_content = dist.get_wheel()

		wheel_platform_tags = set()
		for w_tag in wheel_file_content.get_all("Tag"):
			for tag in parse_tag(w_tag):
				wheel_platform_tags.add(tag.platform)

		tag_intersection = supported_tags.intersection(wheel_platform_tags)
		if not tag_intersection:
			num_tags = len(wheel_platform_tags)
			print(
					f"WARNING: {dist.name} {dist.version} is not supported by this platform.\n",
					f"        {_supported_platforms(num_tags)} {word_join(sorted(wheel_platform_tags), use_repr=True)}.",
					)
			ret = 1

	return ret


@option("-p", "--path", required=True, multiple=True)
@flag_option(
		"-t",
		"--tags",
		help="Print the supported platform tags, one per line, and exit.",
		callback=print_tags,
		expose_value=False,
		is_eager=True,
		)
@click_command()
def main(path: Tuple[str, ...]):
	sys.exit(check(path))


if __name__ == "__main__":
	main()
