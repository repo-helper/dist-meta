===========================
Using :mod:`dist_meta`
===========================

.. module:: dist_meta

:mod:`dist_meta` is a library that provides for access to installed package metadata,
and parsers for ``METADATA`` and ``entry_points.txt`` files.
The library provides similar functionality to :mod:`importlib.metadata`, entrypoints_, and :mod:`email.parser`

Overview
------------

This example demonstrates how to obtain information about an installed distribution, such as its version number,
summary and requirements.

First, create a fresh virtual environment [1]_ and install wheel_:

.. inline-tab:: Unix/macOS

	.. prompt:: bash

		python3 -m virtualenv example
		source example/bin/activate

.. inline-tab:: Windows

	.. code-block:: powershell

		py -m virtualenv example
		.\\example\\Scripts\\activate.ps1

.. [1] See the `Python Packaging User Guide`_ for more details.

.. code-block:: bash

	(example) $ pip install wheel

You can get the :class:`dist_meta.distributions.Distribution` object for ``wheel``
with the :func:`dist_meta.distributions.get_distribution` function:

.. inline-tab:: Unix/macOS

	.. prompt:: bash

		python3

.. inline-tab:: Windows

	.. code-block:: powershell

		py

.. code-block:: pycon

	>>> from dist_meta.distributions import get_distribution
	>>> wheel_dist = get_distribution("wheel")
	>>> wheel_dist
	<Distribution('wheel', <Version('0.36.2')>)>
	>>> wheel_dist.name
	'wheel'
	>>> wheel_dist.version
	<Version('0.36.2')>

Metadata
^^^^^^^^^^

The metadata_ for ``wheel`` can then be obtained as follows:

.. code-block:: pycon

	>>> meta = wheel_dist.get_metadata()
	>>> meta
	<MetadataMapping({'Metadata-Version': '2.1', 'Name': 'wheel', 'Version': '0.36.2', ...})>
	>>> meta["Name"]
	'wheel'
	>>> meta["Version"]
	'0.36.2'
	>>> meta["License"]
	'MIT'
	>>> meta["Summary"]
	'A built-package format for Python'

This is a :class:`dist_meta.metadata_mapping.MetadataMapping` object.
See the `Python Packaging User Guide <metadata>`__ for details of all supported fields.

Some fields may have only a placeholder value [2]_, and others may be absent:

.. code-block:: pycon

	>>> meta["Platform"]
	'UNKNOWN'
	>>> meta["Obsoletes-Dist"]
	Traceback (most recent call last):
	KeyError: 'Obsoletes-Dist'

.. [2] This is a convention of the build tool and not part of :pep:`566`


Requirements
^^^^^^^^^^^^^^^^^^^^

The distribution's requirements (if any) can be obtained from the ``'Requires-Dist'`` field:

.. code-block:: pycon

	>>> requirements = meta.get_all("Requires-Dist")
	>>> requirements
	["pytest (>=3.0.0) ; extra == 'test'", "pytest-cov ; extra == 'test'"]

These can be converted into :class:`packaging.requirements.Requirement` or
:class:`shippinglabel.requirements.ComparableRequirement` objects easily:

.. code-block:: pycon

	>>> from packaging.requirements import Requirement
	>>> list(map(Requirement, requirements))
	[<Requirement('pytest>=3.0.0; extra == "test"')>, <Requirement('pytest-cov; extra == "test"')>]

Some distributions have no requirements:

.. code-block:: pycon

	>>> get_distribution("pip").get_metadata().get_all("Requires-Dist", default=[])
	[]


Missing Distributions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the distribution can't be found, a :class:`dist_meta.distributions.DistributionNotFoundError` is raised:

.. code-block:: pycon

	>>> get_distribution("spamspamspam")
	Traceback (most recent call last):
	dist_meta.distributions.DistributionNotFoundError: spamspamspam

Iterating over Distributions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All installed distributions can be iterated over using the :func:`dist_meta.distributions.iter_distributions` function.
This can be useful to find distributions which meet a particular criteria.

For example, to find all ``sphinxcontrib*`` distributions:

.. code-block:: pycon

	>>> from dist_meta.distributions import iter_distributions
	>>> for distro in iter_distributions():
	...     if distro.name.startswith("sphinxcontrib"):
	...         print(distro)
	<Distribution('sphinxcontrib_applehelp', <Version('1.0.2')>)>
	<Distribution('sphinxcontrib_htmlhelp', <Version('2.0.0')>)>
	<Distribution('sphinxcontrib_jsmath', <Version('1.0.1')>)>
	<Distribution('sphinxcontrib_serializinghtml', <Version('1.1.5')>)>
	<Distribution('sphinxcontrib_qthelp', <Version('1.0.3')>)>
	<Distribution('sphinxcontrib_devhelp', <Version('1.0.2')>)>


Entry Points
------------------

`Entry points`_ are a mechanism for an installed distribution to advertise components it provides
for discovery and used by other code. For example:

* Distributions can specify console_scripts entry points, each referring to a function. When pip_ installs the distribution, it will create a command-line wrapper for each entry point.
* Applications can use entry points to load plugins; e.g. Pygments (a syntax highlighting tool) can use additional lexers and styles from separately installed packages.

Entry points are arranged into groups, such as ``console_scripts`` or ``whey.builder``.

To obtain the entry points for a :class:`~.Distribution`, call its :meth:`~.Distribution.get_entry_points` method:

.. code-block:: pycon

	>>> wheel_dist
	<Distribution('wheel', <Version('0.36.2')>)>
	>>> entry_points = wheel_dist.get_entry_points()
	>>> entry_points.keys()
	dict_keys(['console_scripts', 'distutils.commands'])

This returns a mapping of group names (as strings) to a mapping of entry point names to values (both strings):

.. code-block:: pycon

	>>> from pprint import pprint
	>>> pprint(entry_points)
	{'console_scripts': {'wheel': 'wheel.cli:main'},
	 'distutils.commands': {'bdist_wheel': 'wheel.bdist_wheel:bdist_wheel'}}


:class:`dist_meta.entry_points.EntryPoint` objects can be constructed as follows:

.. code-block:: pycon

	>>> from dist_meta.entry_points import EntryPoint
	>>> for ep in EntryPoint.from_mapping(entry_points["console_scripts"], group="console_scripts"):
	... 	ep
	EntryPoint(name='wheel', value='wheel.cli:main', group='console_scripts', distro=None)

.. TODO: These should be xrefs to the indiv. attributes once fixed in sphinx-toolbox

:class:`dist_meta.entry_points.EntryPoint` objects have attributes for accessing the
``name``, ``module`` and ``attribute`` of the entry point:

.. code-block:: pycon

	>>> ep.name
	'wheel'
	>>> ep.value
	'wheel.cli:main'
	>>> ep.module
	'wheel.cli'
	>>> ep.attr
	'main'
	>>> ep.extras
	[]

The object referred to by the entry point can be loaded using the :meth:`~.EntryPoint.load` method:

.. code-block:: pycon

	>>> main = ep.load()
	>>> main
	<function main at 0x7f4a4bcf94c0>

Entry points for all distributions can be obtained using :func:`dist_meta.entry_points.get_entry_points`
and :func:`dist_meta.entry_points.get_all_entry_points`. The former is used to obtain entry points in a specific group,
while the latter will return all entry points grouped in a dictionary.

.. code-block:: pycon

	>>> from dist_meta.entry_points import get_entry_points, get_all_entry_points
	>>> eps = list(get_entry_points("console_scripts"))
	>>> eps[0]
	EntryPoint(name='tabulate', value='tabulate:_main', group='console_scripts', distro=<Distribution('tabulate', <Version('0.8.9')>)>)
	>>> all_eps = get_all_entry_points()
	>>> all_eps.keys()
	dict_keys(['pytest11', 'console_scripts', 'sphinx.html_themes', 'distutils.commands', 'distutils.setup_keywords', 'babel.checkers', 'babel.extractors', 'flake8.extension', 'flake8.report', 'egg_info.writers', 'setuptools.finalize_distribution_options'])


``RECORD`` files
----------------------

The contents of ``RECORD`` files, which specify the contents of a distribution, can be obtained as follows:

.. code-block:: pycon

	>>> wheel_dist
	<Distribution('wheel', <Version('0.36.2')>)>
	>>> record = wheel_dist.get_record()
	>>> record[2]
	RecordEntry('wheel-0.36.2.dist-info/LICENSE.txt', hash=FileHash(name='sha256', value='zKniDGrx_Pv2lAjzd3aShsvuvN7TNhAMm0o_NfvmNeQ'), size=1125, distro=<Distribution('wheel', <Version('0.36.2')>)>)

``record`` is a list of :class:`dist_meta.record.RecordEntry` objects,
which is a subclasses of :class:`pathlib.PurePosixPath` with additional :attr:`~.RecordEntry.size`,
:attr:`~.RecordEntry.hash` and :attr:`~.RecordEntry.distro` attributes.
The content of a file can be obtained using its :meth:`~.RecordEntry.read_text` or :meth:`~.RecordEntry.read_bytes`:

.. code-block:: pycon

	>>> print(record[2].read_text()[:100])
	"wheel" copyright (c) 2012-2014 Daniel Holth <dholth@fastmail.fm> and
	contributors.
	<BLANKLINE>
	The MIT License

If the ``RECORD`` file is absent, :meth:`~.Distribution.get_record` will return :py:obj:`None`.

.. _metadata: https://packaging.python.org/specifications/core-metadata/
.. _wheel: https://pypi.org/project/wheel/
.. _Python Packaging User Guide: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments
.. _pip: https://pypi.org/project/pip/
.. _entrypoints: https://github.com/takluyver/entrypoints/
.. _Entry points: https://packaging.python.org/specifications/entry-points/?highlight=entry%20points
