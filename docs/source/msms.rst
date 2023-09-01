``LipidIMEA.msms``
=======================================
This subpackage has utilities for analyzing MS/MS data. There are general utility functions
than can be imported directly from ``LipidIMEA.msms`` module, and functions for analyzing
DDA or DIA data from the ``LipidIMEA.msms.dda`` or ``LipidIMEA.msms.dda`` submodules, 
respectively.

Module Reference
---------------------------------------

Utility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``create_results_db``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.create_results_db

``load_default_params``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.load_default_params

``load_params``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.load_params

``save_params``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.save_params

``debug_handler``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms._util.debug_handler


DDA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``extract_dda_features``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dda.extract_dda_features

``extract_dda_features_multiproc``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dda.extract_dda_features_multiproc

``consolidate_dda_features``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dda.consolidate_dda_features


DIA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``extract_dia_features``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dia.extract_dia_features

``extract_dia_features_multiproc``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dia.extract_dia_features_multiproc
