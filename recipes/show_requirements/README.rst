========================
``show_requirements.py``
========================

This script lists requirements for the given package, based on installed packages, using metadata in ``.dist-info/METADATA``.


Usage
===========

.. code-block:: bash

	python3 show_requirements.py domdf_python_tools


Example output::

	domdf_python_tools==3.3.0
	├── importlib-metadata (>=3.6.0) ; python_version < "3.9"
	│   └── zipp>=0.5
	├── importlib-resources (>=3.0.0) ; python_version < "3.7"
	│   └── zipp>=3.1.0; python_version < "3.10"
	├── natsort (>=7.0.1)
	├── pytz (>=2019.1) ; extra == 'all'
	├── pytz (>=2019.1) ; extra == 'dates'
	└── typing-extensions (>=3.7.4.1)
