# stdlib
from typing import Union

# 3rd party
from coincidence.regressions import _representer_for
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pytest_regressions.data_regression import RegressionYamlDumper


@_representer_for(str, Version, Requirement, Marker, SpecifierSet)
def represent_packaging_types(
		dumper: RegressionYamlDumper,
		data: Union[Version, Requirement, Marker, SpecifierSet],
		):
	return dumper.represent_str(str(data))
