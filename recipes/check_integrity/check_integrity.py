"""
Check files match the checksums given in RECORD.
"""

# stdlib
import sys
import time
from typing import List, Optional, Tuple

# 3rd party
import click
from shippinglabel.checksum import get_sha256_hash

# this package
import dist_meta


def check_distribution(dist_name: str, path: Optional[Tuple[str, ...]] = None) -> int:
	"""
	Verify the integrity of the distribution named ``dist_name``.

	The distribution must be installed.

	:param dist_name:
	:param path: A list of Python directories to find the distribution in. Akin to :py:obj:`sys.path`.

	:return: ``0`` if the distribution verifies successfully,
		``1`` if it fails or files are missing.
	"""

	try:
		dist = dist_meta.distributions.get_distribution(dist_name, path)
	except dist_meta.distributions.DistributionNotFoundError:
		print(f"No distribution named {dist_name!r}.")
		return 1

	record = dist.get_record()
	if record is None:
		# Missing file
		print(f"Unable to verify integrity of {dist_name!r}: RECORD file not found.")
		return 1

	print(f"Verifying integrity of distribution {dist_name!r}", end='', flush=True)
	has_errored = False

	dist_basepath = dist.path
	for entry in record:
		time.sleep(.01)

		# The absolute path to the file given in the RECORD entry.
		the_filename = (dist_basepath.parent / entry).abspath()

		if entry.hash:
			# Not all files have a hash in RECORD
			expected_hash = entry.hash.hexdigest()
			actual_hash = get_sha256_hash(the_filename).hexdigest()

			if expected_hash != actual_hash:
				if not has_errored:
					print()
					has_errored = True

				print(f"Hash mismatch: {entry}")
				print(f"    Expected {expected_hash!r}")
				print(f"    Got      {actual_hash!r}")

	if has_errored:
		print()
		return 1
	else:
		print(" ✔️")
		return 0


def main(argv: List[str]) -> int:
	"""
	CLI entry point.

	:param argv: List of arguments à la ``sys.argv``.

	:return:
	"""


@click.option("-p", "--path", required=False, multiple=True)
@click.argument("name", nargs=-1, type=str)
@click.command()
def main(name: Tuple[str], path: Tuple[str, ...]):
	# Exit codes:
	# 	0 if all distributions verify successfully,
	# 	1 if any fail or are missing files
	# 	2 if no arguments are passed

	if not name:
		sys.exit(2)

	if not path:
		path = None

	ret = 0

	for dist_name in name:
		ret |= check_distribution(dist_name, path)

	sys.exit(ret)


if __name__ == "__main__":
	main()
