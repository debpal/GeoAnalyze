============
Quickstart
============

This guide provides a quick overview to help you get started with the :mod:`GeoAnalyze`.


Verify Installation
---------------------

To verify installation, import the module and initialize the :class:`GeoAnalyze.File` class using the following code.
If no errors are raised, the installation has been successful.


.. code-block:: python

    import GeoAnalyze
    file = GeoAnalyze.File()
    
    
Performing File Operations
----------------------------

In geospatial processing, a shapefile such as `original.shp` typically has associated files like `original.cpg`, `original.dbf`, `original.prj`, and `original.shx`.
These files are critical for the shapefile to function properly. Below are examples of common file operations that can be performed on a shapefile and its associated files.
    

Renaming Files
^^^^^^^^^^^^^^^^

To rename `original.shp` and its associated files, you can use the following code. This ensures that all related files are renamed consistently.

.. code-block:: python

    file.name_change(
        folder_path=r"C:\users\username\folder",
        rename_map={'original': 'rename'}
    )
    
    
    
Transferring Files
^^^^^^^^^^^^^^^^^^^^

To move the renamed shapefile `rename.shp` and its associated files from the source folder to the destination folder, the following code can be used.
This will ensure the specified files are transferred correctly based on the provided names.

.. code-block:: python

    file.transfer_by_name(
        src_folder=r"C:\users\username\src_folder",
        dst_folder=r"C:\users\username\dst_folder",
        file_names=['rename']
    )
    
    
Deleting files
^^^^^^^^^^^^^^^^^

To delete the shapefile `rename.shp` and all its associated files from a folder, use the following code.

.. code-block:: python

    file.delete_by_name(
        folder_path=r"C:\users\username\dst_folder",
        file_names=['rename']
    )


    
    


    