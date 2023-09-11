``LipidIMEA.msms``
=======================================
This subpackage has utilities for analyzing MS/MS data. There are functions for analyzing
DDA or DIA data from the ``LipidIMEA.msms.dda`` or ``LipidIMEA.msms.dda`` submodules, 
respectively.

Module Reference
---------------------------------------

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


``add_calibrated_ccs_to_dia_features``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.msms.dia.add_calibrated_ccs_to_dia_features
