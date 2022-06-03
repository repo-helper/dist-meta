========================
``check_integrity.py``
========================

This script checks files for installed distributions match the checksums given in ``.dist-info/RECORD``.


Usage
===========

.. code-block:: bash

	python3 check_integrity.py pip dist_meta apeye mypy packaging more_itertools
	python3 check_integrity.py packaging --path venv/lib/python3.8/site-packages
	python3 check_integrity.py packaging -p venv/lib/python3.8/site-packages -p /usr/lib/python3.8/site-packages


Example output::

	Verifying integrity of distribution 'pip'
	Hash mismatch: pip/__main__.py
		Expected '997c160dfb4d2cc29fc15a8a156184feeb8166f1922225042e12e47b2b08b997'
		Got      'c8e4a345f63f7d0b5f1e5cf5f58e9eb76dcb65210f50ee6a37ade0034650c5b4'

	Verifying integrity of distribution 'dist_meta' ✔️
	Verifying integrity of distribution 'apeye' ✔️
	Verifying integrity of distribution 'mypy'
	Hash mismatch: ../../../bin/mypyc
		Expected 'd4a33575e8881edd5cd6c6d132ff56e527696713d820741e8b7b7e058a35fcc9'
		Got      '6f8a14c35efe65303d9ab2b31449411d741fcf988b389ed073491dd46b88ad5d'

	Verifying integrity of distribution 'packaging' ✔️
	Verifying integrity of distribution 'more_itertools' ✔️
