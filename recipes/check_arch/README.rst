========================
``check_arch.py``
========================

This script checks installed wheels have the correct architecture.


Usage
===========

.. code-block:: bash

	python3 check_arch.py -p venv/lib/python3.8/site-packages/


Example output::

	WARNING: regex 2022.3.15 is not supported by this platform.
			The platform it supports is 'macosx_10_9_x86_64'


To list suppoorted platform tags:

.. code-block:: bash

	python3 check_arch.py -t


Example output::

	any
	linux_x86_64
	manylinux1_x86_64
	manylinux2010_x86_64
	manylinux2014_x86_64
