==============
Installation
==============

The installation of the package is straightforward. To prevent conflicts with other Python packages, it is recommended to create a separate Python environment. 
Below are the steps for installing the package using different methods.


Create a Python environment
-----------------------------

Suppose your environment name is `env_ga`, and you can create it by using the following steps through Anaconda distribution.

.. code-block:: console
    
    conda create --name env_ga
    conda activate env_ga
    conda install pip


Install from PyPI
-------------------

.. code-block:: console
    
    pip install GeoAnalyze



Install from GitHub repository
--------------------------------

.. code-block:: console

    pip install git+https://github.com/debpal/GeoAnalyze.git
    
    
Install from source code in editable mode
--------------------------------------------

For developers who want to modify the source code or contribute to the package, it is recommended to install in editable mode.
Navigate to your directory with the `env_ga` Python environemnt activated, and run the following commands. 
This allows you to make changes to the source code, with immediate reflection in the `env_ga` environment without requiring reinstallation.

.. code-block:: console

    pip install build
    git clone https://github.com/debpal/GeoAnalyze.git
    cd GeoAnalyze
    python -m build
    pip install -e .
