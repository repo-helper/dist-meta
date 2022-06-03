==========
dist-meta
==========

.. start short_desc

**Parse and create Python distribution metadata.**

.. end short_desc


.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Anaconda
	  - |conda-version| |conda-platform|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/dist-meta/latest?logo=read-the-docs
	:target: https://dist-meta.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/repo-helper/dist-meta/workflows/Docs%20Check/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/repo-helper/dist-meta/workflows/Linux/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/repo-helper/dist-meta/workflows/Windows/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/repo-helper/dist-meta/workflows/macOS/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/repo-helper/dist-meta/workflows/Flake8/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/repo-helper/dist-meta/workflows/mypy/badge.svg
	:target: https://github.com/repo-helper/dist-meta/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.herokuapp.com/github/repo-helper/dist-meta/badge.svg
	:target: https://dependency-dash.herokuapp.com/github/repo-helper/dist-meta/
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/repo-helper/dist-meta/master?logo=coveralls
	:target: https://coveralls.io/github/repo-helper/dist-meta?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/repo-helper/dist-meta?logo=codefactor
	:target: https://www.codefactor.io/repository/github/repo-helper/dist-meta
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/dist-meta
	:target: https://pypi.org/project/dist-meta/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/dist-meta?logo=python&logoColor=white
	:target: https://pypi.org/project/dist-meta/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/dist-meta
	:target: https://pypi.org/project/dist-meta/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/dist-meta
	:target: https://pypi.org/project/dist-meta/
	:alt: PyPI - Wheel

.. |conda-version| image:: https://img.shields.io/conda/v/domdfcoding/dist-meta?logo=anaconda
	:target: https://anaconda.org/domdfcoding/dist-meta
	:alt: Conda - Package Version

.. |conda-platform| image:: https://img.shields.io/conda/pn/domdfcoding/dist-meta?label=conda%7Cplatform
	:target: https://anaconda.org/domdfcoding/dist-meta
	:alt: Conda - Platform

.. |license| image:: https://img.shields.io/github/license/repo-helper/dist-meta
	:target: https://github.com/repo-helper/dist-meta/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/repo-helper/dist-meta
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/repo-helper/dist-meta/v0.5.0
	:target: https://github.com/repo-helper/dist-meta/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/repo-helper/dist-meta
	:target: https://github.com/repo-helper/dist-meta/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2022
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/dist-meta
	:target: https://pypi.org/project/dist-meta/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``dist-meta`` can be installed from PyPI or Anaconda.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install dist-meta

To install with ``conda``:

	* First add the required channels

	.. code-block:: bash

		$ conda config --add channels https://conda.anaconda.org/conda-forge
		$ conda config --add channels https://conda.anaconda.org/domdfcoding

	* Then install

	.. code-block:: bash

		$ conda install dist-meta

.. end installation
