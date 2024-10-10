============
Quickstart
============

This guide provides a quick overview to get started with :mod:`GeoAnalyze`.


Verify Installation
---------------------
Ensure successful installation by running the following commands:

.. code-block:: python

    import GeoAnalyze
    file = GeoAnalyze.file()
    
    
Delete File
-------------
Deleting files with the same name in a folder, irrespective of extensions, if the file exists.

.. code-block:: python

    file.delete_by_name(
        folder_path=r"C:\Users\Username\Folder",
        file_names=['test']
    )
    
Expected output:

.. code-block:: text

    "List of deleted files: ['test.cpg', 'test.dbf', 'test.prj', 'test.shp', 'test.shx']."

    