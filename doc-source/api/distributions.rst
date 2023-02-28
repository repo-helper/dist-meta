=================================
:mod:`dist_meta.distributions`
=================================

.. autosummary-widths:: 6/16

.. automodule:: dist_meta.distributions
	:no-members:
	:autosummary-members:
	:member-order: bysource

.. autofunction:: dist_meta.distributions.get_distribution
.. autofunction:: dist_meta.distributions.iter_distributions
.. autofunction:: dist_meta.distributions.packages_distributions

.. autoclass:: dist_meta.distributions.DistributionType
	:no-show-inheritance:
	:member-order: bysource
	:private-members:

.. autonamedtuple:: dist_meta.distributions.Distribution
	:no-show-inheritance:
	:member-order: bysource
	:exclude-members: __repr__

	Bases: :class:`~.DistributionType`

.. autonamedtuple:: dist_meta.distributions.WheelDistribution
	:no-show-inheritance:
	:member-order: bysource
	:exclude-members: __repr__

	Bases: :class:`~.DistributionType`

.. autoexception:: dist_meta.distributions.DistributionNotFoundError
.. autotypevar:: dist_meta.distributions._DT
