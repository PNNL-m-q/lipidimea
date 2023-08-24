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

.. autofunction:: LipidIMEA.msms.create_lipid_ids_db

.. autofunction:: LipidIMEA.msms.load_params

DDA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: LipidIMEA.msms.dda.extract_dda_features

.. autofunction:: LipidIMEA.msms.dda.extract_dda_features_multiproc

.. autofunction:: LipidIMEA.msms.dda.consolidate_dda_features

DIA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: LipidIMEA.msms.dia.extract_dia_features

.. autofunction:: LipidIMEA.msms.dia.extract_dia_features_multiproc
