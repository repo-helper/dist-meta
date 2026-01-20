==========
dist-meta
==========

.. start short_desc

.. documentation-summary::
	:meta:

.. end short_desc

.. start shields

.. only:: html

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

	.. |docs| rtfd-shield::
		:project: dist-meta
		:alt: Documentation Build Status

	.. |docs_check| actions-shield::
		:workflow: Docs Check
		:alt: Docs Check Status

	.. |actions_linux| actions-shield::
		:workflow: Linux
		:alt: Linux Test Status

	.. |actions_windows| actions-shield::
		:workflow: Windows
		:alt: Windows Test Status

	.. |actions_macos| actions-shield::
		:workflow: macOS
		:alt: macOS Test Status

	.. |actions_flake8| actions-shield::
		:workflow: Flake8
		:alt: Flake8 Status

	.. |actions_mypy| actions-shield::
		:workflow: mypy
		:alt: mypy status

	.. |requires| image:: https://dependency-dash.repo-helper.uk/github/repo-helper/dist-meta/badge.svg
		:target: https://dependency-dash.repo-helper.uk/github/repo-helper/dist-meta/
		:alt: Requirements Status

	.. |coveralls| coveralls-shield::
		:alt: Coverage

	.. |codefactor| codefactor-shield::
		:alt: CodeFactor Grade

	.. |pypi-version| pypi-shield::
		:project: dist-meta
		:version:
		:alt: PyPI - Package Version

	.. |supported-versions| pypi-shield::
		:project: dist-meta
		:py-versions:
		:alt: PyPI - Supported Python Versions

	.. |supported-implementations| pypi-shield::
		:project: dist-meta
		:implementations:
		:alt: PyPI - Supported Implementations

	.. |wheel| pypi-shield::
		:project: dist-meta
		:wheel:
		:alt: PyPI - Wheel

	.. |conda-version| image:: https://img.shields.io/conda/v/conda-forge/dist-meta?logo=anaconda
		:target: https://anaconda.org/conda-forge/dist-meta
		:alt: Conda - Package Version

	.. |conda-platform| image:: https://img.shields.io/conda/pn/conda-forge/dist-meta?label=conda%7Cplatform
		:target: https://anaconda.org/conda-forge/dist-meta
		:alt: Conda - Platform

	.. |license| github-shield::
		:license:
		:alt: License

	.. |language| github-shield::
		:top-language:
		:alt: GitHub top language

	.. |commits-since| github-shield::
		:commits-since: v0.9.0
		:alt: GitHub commits since tagged version

	.. |commits-latest| github-shield::
		:last-commit:
		:alt: GitHub last commit

	.. |maintained| maintained-shield:: 2026
		:alt: Maintenance

	.. |pypi-downloads| pypi-shield::
		:project: dist-meta
		:downloads: month
		:alt: PyPI - Downloads

.. end shields

Installation
---------------

.. start installation

.. installation:: dist-meta
	:pypi:
	:github:
	:anaconda:
	:conda-channels: conda-forge

.. end installation


Contents
-----------

.. html-section::


.. toctree::
	:hidden:

	Home<self>

.. toctree::
	:maxdepth: 3
	:glob:

	usage
	api/*

.. sidebar-links::
	:caption: Links
	:github:
	:pypi: dist-meta

	Contributing Guide <https://contributing.repo-helper.uk>
	Source
	license


.. start links

.. only:: html

	View the :ref:`Function Index <genindex>` or browse the `Source Code <_modules/index.html>`__.

	:github:repo:`Browse the GitHub Repository <repo-helper/dist-meta>`

.. end links
