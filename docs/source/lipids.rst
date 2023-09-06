``LipidIMEA.lipids``
=======================================
This subpackage defines the ``Lipid`` class and subclass(es) that are used to represent individual lipid 
species. The lipid classification system defined and used by LIPID MAPS is used in this package:

* https://www.lipidmaps.org/data/classification/LM_classification_exp.php 
* https://www.jlr.org/article/S0022-2275(20)30580-0/fulltext

The subpackage also houses utilities for annotating features from the DDA-DIA data analysis.

Module Reference
---------------------------------------

Utility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``parse_lipid_name``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.lipids.parse_lipid_name

``Lipid`` and ``LipidWithChains``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: LipidIMEA.lipids.Lipid

.. autofunction:: LipidIMEA.lipids.Lipid.__init__

.. autoclass:: LipidIMEA.lipids.LipidWithChains

.. autofunction:: LipidIMEA.lipids.LipidWithChains.__init__

.. autofunction:: LipidIMEA.lipids.LipidWithChains.add_db_positions


Annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SumCompLipidDB``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: LipidIMEA.lipids.annotation.SumCompLipidDB

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.__init__

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.fill_db_from_config

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.get_sum_comp_lipid_ids

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.gen_sum_compositions

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.max_u

.. autofunction:: LipidIMEA.lipids.annotation.SumCompLipidDB.close

``remove_lipid_annotations``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.lipids.annotation.remove_lipid_annotations

``annotate_lipid_sum_composition``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: LipidIMEA.lipids.annotation.annotate_lipids_sum_composition
