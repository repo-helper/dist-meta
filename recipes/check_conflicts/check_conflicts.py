"""
Check packages for version and architecture conflicts.
"""

# stdlib
import sys
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union

# 3rd party
import click
from domdf_python_tools.words import Plural, PluralPhrase, word_join
from natsort import natsorted
from packaging.requirements import Requirement
from packaging.tags import parse_tag, platform_tags
from packaging.utils import NormalizedName, canonicalize_name
from packaging.version import LegacyVersion, Version

# this package
from dist_meta.distributions import Distribution, iter_distributions

supported_tags = set(platform_tags())
supported_tags.add("any")

_supported_platforms = PluralPhrase(
		"The {} it supports {}",
		(Plural("platform", "platforms"), Plural("is", "are")),
		)


def print_tags(ctx, param, tags: bool = False):
	if not tags or ctx.resilient_parsing:
		return
	print('\n'.join(natsorted(supported_tags)))
	ctx.exit()


DistributionVersion = Union[LegacyVersion, Version]


class PackageDetails(NamedTuple):
	version: DistributionVersion
	dependencies: List[Requirement]
	wheel_platform_tags: Set[str]


# Shorthands
PackageSet = Dict[NormalizedName, PackageDetails]
Missing = Tuple[NormalizedName, Requirement]
Conflicting = Tuple[NormalizedName, DistributionVersion, Requirement]

MissingDict = Dict[NormalizedName, List[Missing]]
ConflictingDict = Dict[NormalizedName, List[Conflicting]]
ArchMismatchDict = Dict[NormalizedName, Set[str]]
CheckResult = Tuple[MissingDict, ConflictingDict, ArchMismatchDict]


def get_wheel_platform_tags(dist: Distribution) -> Set[str]:
	"""
	Returns a list of wheel platform tags (i.e. the supported platforms) for the given distribution.

	:param dist:
	:return:
	"""

	wheel_platform_tags = set()
	wheel_file_content = dist.get_wheel()

	if wheel_file_content:
		# Might not have a WHEEL file; might not be installed from a wheel.

		for w_tag in wheel_file_content.get_all("Tag", ()):
			for tag in parse_tag(w_tag):
				wheel_platform_tags.add(tag.platform)

	return wheel_platform_tags


def create_package_set_from_installed(path) -> Tuple[PackageSet, bool]:
	"""
	Converts a list of distributions into a PackageSet.

	:param path: A list of Python directories to find dependencies in. Akin to :py:obj:`sys.path`.
	"""

	package_set: PackageSet = {}
	parsing_probs = False

	for dist in iter_distributions(path):
		name = canonicalize_name(dist.name)

		try:
			# TODO: extras?
			raw_dependencies = dist.get_metadata().get_all("Requires-Dist", default=())
			package_set[name] = PackageDetails(
					version=dist.version,
					dependencies=list(map(Requirement, raw_dependencies)),
					wheel_platform_tags=get_wheel_platform_tags(dist),
					)

		except (OSError, ValueError) as e:
			# Don't crash on unreadable or broken metadata.
			print(f"Error parsing requirements for {name}: {e}")
			parsing_probs = True

	return package_set, parsing_probs


def get_conflicts(package_set: PackageSet) -> CheckResult:
	"""
	Identify conflicting dependencies and architectures, and missing packages, in the package set.

	:param package_set:
	"""

	missing: MissingDict = {}
	conflicting: ConflictingDict = {}
	arch_mismatch: ArchMismatchDict = {}

	for package_name, package_detail in package_set.items():
		# Info about dependencies of package_name
		missing_deps: Set[Missing] = set()
		conflicting_deps: Set[Conflicting] = set()

		for req in package_detail.dependencies:
			name = canonicalize_name(req.name)

			# Check if it's missing
			if name not in package_set:
				missed = True
				if req.marker is not None:
					missed = req.marker.evaluate({"extra": None})

				if missed:
					missing_deps.add((name, req))

				continue

			elif req.marker is not None and not req.marker.evaluate({"extra": None}):
				continue

			# Check if there's a conflict
			version = package_set[name].version
			if not req.specifier.contains(version, prereleases=True):
				conflicting_deps.add((name, version, req))

		if missing_deps:
			missing[package_name] = sorted(missing_deps, key=str)
		if conflicting_deps:
			conflicting[package_name] = sorted(conflicting_deps, key=str)

		tag_intersection = supported_tags.intersection(package_detail.wheel_platform_tags)
		if not tag_intersection:
			arch_mismatch[package_name] = package_detail.wheel_platform_tags

	return missing, conflicting, arch_mismatch


def check(path: Optional[Tuple[str, ...]] = None) -> int:
	"""
	Check packages for version and architecture conflicts.

	:param path: A list of Python directories to find dependencies in. Akin to :py:obj:`sys.path`.

	:return: ``0`` if there are no conflicts, ``1`` if there are conflicts or parsing errors.
	"""

	package_set, parsing_probs = create_package_set_from_installed(path)
	missing, conflicting, arch_mismatch = get_conflicts(package_set)

	for project_name in missing:
		version = package_set[project_name].version
		for dependency in missing[project_name]:
			print(f"{project_name} {version} requires {dependency[0]}, which is not installed.")

	for project_name in conflicting:
		version = package_set[project_name].version
		for dep_name, dep_version, req in conflicting[project_name]:
			print(f"{project_name} {version} has requirement {req}, but you have {dep_name} {dep_version}.")

	for project_name in arch_mismatch:
		version = package_set[project_name].version
		wheel_platform_tags = arch_mismatch[project_name]
		num_tags = len(wheel_platform_tags)
		print(
				f"{project_name} {version} is not supported by this platform.\n",
				f"        {_supported_platforms(num_tags)} {word_join(sorted(wheel_platform_tags), use_repr=True)}.",
				)

	if any((missing, conflicting, arch_mismatch, parsing_probs)):
		return 1
	else:
		print("No broken requirements found.")
		return 0


@click.option("-p", "--path", required=False, multiple=True)
@click.option(
		"-t",
		"--tags",
		help="Print the supported platform tags, one per line, and exit.",
		callback=print_tags,
		expose_value=False,
		is_eager=True,
		is_flag=True,
		)
@click.command()
def main(path: Tuple[str, ...]):
	if not path:
		path = None

	sys.exit(check(path))


if __name__ == "__main__":
	main()
