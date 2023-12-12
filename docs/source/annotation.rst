``lipidimea.annotation``
=======================================
This module houses utilities for annotating features from the DDA-DIA data analysis.


Annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SumCompLipidDB``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: lipidimea.annotation.SumCompLipidDB

.. autofunction:: lipidimea.annotation.SumCompLipidDB.__init__

.. autofunction:: lipidimea.annotation.SumCompLipidDB.fill_db_from_config

.. autofunction:: lipidimea.annotation.SumCompLipidDB.get_sum_comp_lipid_ids

.. autofunction:: lipidimea.annotation.SumCompLipidDB.gen_sum_compositions

.. autofunction:: lipidimea.annotation.SumCompLipidDB.max_u

.. autofunction:: lipidimea.annotation.SumCompLipidDB.close

``remove_lipid_annotations``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.annotation.remove_lipid_annotations

``annotate_lipid_sum_composition``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.annotation.annotate_lipids_sum_composition

``filter_annotations_by_rt_range``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: lipidimea.annotation.filter_annotations_by_rt_range
