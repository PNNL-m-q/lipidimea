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

.. autofunction:: LipidIMEA.lipids.parse_lipid_name

.. autoclass:: LipidIMEA.lipids.Lipid

.. autofunction:: LipidIMEA.lipids.Lipid.__init__

.. autoclass:: LipidIMEA.lipids.LipidWithChains

.. autofunction:: LipidIMEA.lipids.LipidWithChains.__init__

.. autofunction:: LipidIMEA.lipids.LipidWithChains.add_db_positions


Annotation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LipidIMEA.lipids.annotation._SumCompLipidDB

.. autofunction:: LipidIMEA.lipids.annotation._SumCompLipidDB.__init__

.. autofunction:: LipidIMEA.lipids.annotation._SumCompLipidDB.get_sum_comp_lipid_ids

.. autofunction:: LipidIMEA.lipids.annotation._SumCompLipidDB.close
