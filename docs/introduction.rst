==============
Introduction
==============    
    
:mod:`GeoAnalyze` is a Python package designed to streamline geoprocessing by handling internal complexities and intermediate steps. Conceptualized and launched on October 10, 2024, this package is tailored for users with limited geospatial processing experience, allowing them to focus on desired outputs. Leveraging open-source geospatial Python modules, GeoAnalyze aims to empower users by providing high-level geoprocessing tools with fewer lines of code. This fast package is also useful for the users who has no access of paid GIS software packages.  


Wateshed Delineation
--------------------------

The :class:`GeoAnalyze.Watershed` and :class:`GeoAnalyze.Stream` classes provide fast and scalable watershed delineation functions by leveraging the computational efficiency of the PyPI package `pyflwdir  <https://github.com/Deltares/pyflwdir>`_, without requiring a detailed understanding of it. These functions can be executed either individually or simultaneously.

*Hydrology*
^^^^^^^^^^^^^^^^^^

- Basin area extraction from an extended Digital Elevation Model (DEM)
- DEM pit filling
- Slope calculation
- Slope classification
- Aspect determination
- Flow direction mapping
- Flow accumulation computation
- Stream extraction
- Subbasin generation

The computational efficiency of these functions is demonstrated in the following output figure.
All delineation files—including basin area, flow direction, flow accumulation, slope, stream, outlets, and subbasins—can be generated within 30 seconds from a raster containing 14 million cells.
Please refer to the :ref:`Watershed Delineation <watershed_delineation>` section or more details.

.. image:: _static/dem_all_delineation.png
   :align: center
   
.. raw:: html

   <br><br>


*Stream Network*
^^^^^^^^^^^^^^^^^^^^^^^^

- Determines the adjacent downstream segment for each stream segment
- Retrieves adjacent upstream segments associated with each stream segment
- Builds full connectivity structures from upstream to downstream
- Computes connectivity structures from downstream to upstream
- Removes all upstream connectivity up to headwaters for targeted stream segments
- Merges stream segments either between two junction points or from a junction point upstream until a headwater is reached
- Detects junctions, drainage points, main outlets, and headwaters within the stream network
- Computes Strahler and Shreve orders of stream segments
- Includes multiple functions for generating random boxes around selected stream segments

Geoprocessing
--------------------

The :mod:`GeoAnalyze` package leverages the existing PyPI packages, such as, `rasterio  <https://github.com/rasterio/rasterio>`_,
`geopandas  <https://github.com/geopandas/geopandas>`_, and `shapely  <https://github.com/shapely/shapely>`_,
to perform geoprocessing efficiently while reducing implementation complexity.
Instead of requiring multiple lines of code to handle intermediate steps,
the :class:`GeoAnalyze.Raster` and :class:`GeoAnalyze.Shape` classes streamline the process by automating these operations.
Furthermore, the :class:`GeoAnalyze.Visual` class assists in raster and vector data plotting and visualization.
This allows users to execute geoprocessing tasks more efficiently, reducing code length while ensuring accuracy and scalability.


*Raster*
^^^^^^^^^^^

- Rasterizing input geometries
- Rescaling raster resolution
- Clipping a raster using a shapefile
- Overlaying geometries onto a raster
- Reprojecting the Coordinate Reference System (CRS)
- Handling NoData values in a raster  
- Generating boundary polygons from a raster
- Reclassifying raster values
- Computing raster statistics
- Counting unique raster values
- Trimming and extending rasters
- Extracting raster values using a mask
- Merging multiple raster files
- Rewriting a raster with a different driver


*Shapefile*
^^^^^^^^^^^^^^^

- Vectorizing a raster array
- Aggregating geometries from multiple shapefiles
- Executing spatial joins on geometries
- Reprojecting the CRS
- Filling polygons
- Performing column operations on a shapefile


*Visualization*

- Quick view of a raster array
- Quick view of shapefile geometries


File Operations (Irrespective of Extensions)
----------------------------------------------

When managing GIS files, each main file is often associated with several auxiliary files. For example, a shapefile
is commonly accompanied by `.shp`, `.cpg`, `.dbf`, `.prj`, and `.shx` files, which are necessary for the shapefile to function correctly.
In geoprocessing, these associated files must be handled together to prevent errors or data loss.
The :class:`GeoAnalyze.File` class simplifies this process by ensuring that any operation performed
on a main file automatically includes its auxiliary files, making file management more efficient and error-free.

* Deleting files in a folder.
* Transferring files from the source folder to the destination folder.
* Renaming files in a folder.
* Copying files from the source folder and renames them in the destination folder.
* Extracting files with the same extension from a folder.