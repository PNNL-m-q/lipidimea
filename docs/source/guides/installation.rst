Installation
==============================

From PyPI
------------------------------
``LipidIMEA`` is installable from the PyPI via `pip <https://pip.pypa.io/en/stable/>`_:

.. code-block::

    pip install LipidIMEA

From Source
------------------------------
The source code can also be cloned from the `GitHub repository <https://github.com/PNNL-m-q/LipidIMEA>`_ and installed 
using `pip <https://pip.pypa.io/en/stable/>`_. This method allows for installation of development versions other than
the stable release version (``main`` branch).

.. code-block::

    # clone latest stable release (main branch)
    git clone https://github.com/PNNL-m-q/LipidIMEA.git
    
    # OR clone the development branch
    git clone --branch dev https://github.com/PNNL-m-q/LipidIMEA.git

    # OR clone a specific feature development branch
    git clone --branch add_multi_dim_filter https://github.com/PNNL-m-q/LipidIMEA.git 
    
    # install
    pip install LipidIMEA/


Dependencies
------------------------------
* ``h5py``
* ``hdf5plugin``
* ``matplotlib``
* ``numpy``
* ``pandas``
* ``scipy``
* ``matplotlib``
