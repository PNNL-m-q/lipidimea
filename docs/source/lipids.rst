``lipidimea.lipids``
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

.. autofunction:: lipidimea.lipids.parse_lipid_name

``Lipid`` and ``LipidWithChains``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: lipidimea.lipids.Lipid

.. autofunction:: lipidimea.lipids.Lipid.__init__

.. autoclass:: lipidimea.lipids.LipidWithChains

.. autofunction:: lipidimea.lipids.LipidWithChains.__init__

.. autofunction:: lipidimea.lipids.LipidWithChains.add_db_positions


Annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SumCompLipidDB``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: lipidimea.lipids.annotation.SumCompLipidDB

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.__init__

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.fill_db_from_config

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.get_sum_comp_lipid_ids

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.gen_sum_compositions

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.max_u

.. autofunction:: lipidimea.lipids.annotation.SumCompLipidDB.close

``remove_lipid_annotations``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.lipids.annotation.remove_lipid_annotations

``annotate_lipid_sum_composition``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.lipids.annotation.annotate_lipids_sum_composition

``filter_annotations_by_rt_range``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.lipids.annotation.filter_annotations_by_rt_range
