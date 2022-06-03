========================
``check_conflicts.py``
========================

This script checks installed distributions for version conflicts, missing dependencies,
and platform/architecture conflicts.


Usage
===========

.. code-block:: bash

	python3 check_conflicts.py
	python3 check_conflicts.py --path venv/lib/python3.8/site-packages
	python3 check_conflicts.py -p venv/lib/python3.8/site-packages -p /usr/lib/python3.8/site-packages


Example output::

	sphinx-toolbox 3.0.0 has requirement sphinx>=3.2.0, but you have sphinx 2.0.0.
	sphinx-autodoc-typehints 1.14.1 has requirement Sphinx>=4, but you have sphinx 2.0.0.
	autodocsumm 0.2.8 has requirement Sphinx<5.0,>=2.2, but you have sphinx 2.0.0.
	markupsafe 2.1.1 is not supported by this platform.
			 The platform it supports is 'macosx_10_9_x86_64'.
