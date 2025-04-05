==============
Introduction
==============    
    
:mod:`GeoAnalyze` is a Python package designed to streamline geoprocessing by handling internal complexities and intermediate steps. Conceptualized and launched on October 10, 2024, this package is tailored for users with limited geospatial processing experience, allowing them to focus on desired outputs. Leveraging open-source geospatial Python modules, GeoAnalyze aims to empower users by providing high-level geoprocessing tools with fewer lines of code. This fast package is also useful for the users who has no access of paid GIS software packages.  


Delineation Functions
--------------------------

The :class:`GeoAnalyze.Watershed` and :class:`GeoAnalyze.Stream` classes provide fast and scalable watershed delineation functions by leveraging the computational efficiency of the PyPI package `pyflwdir  <https://github.com/Deltares/pyflwdir>`_, without requiring a detailed understanding of it. These functions can be executed either individually or simultaneously.

* Basin area extraction from extended Digital Elevation Model (DEM).
* Pit filling of DEM.
* Slope.
* Flow direction.
* Flow accumulation.
* Stream extraction.
* Subbaisn generation.
* Stream link.
* Main outlet and junction points.

The computational efficiency of these functions is demonstrated in the following output figure.
All delineation files—including basin area, flow direction, flow accumulation, slope, stream, outlets, and subbasins—can be generated within 30 seconds from a raster containing 14 million cells.
Please refer to the :ref:`Watershed Delineation <watershed_delineation>` section or more details.

.. image:: _static/dem_all_delineation.png
   :align: center
   
.. raw:: html

   <br><br>



Geoprocessing
--------------------

The :mod:`GeoAnalyze` package leverages the existing PyPI packages, such as, `rasterio  <https://github.com/rasterio/rasterio>`_,
`geopandas  <https://github.com/geopandas/geopandas>`_, and `shapely  <https://github.com/shapely/shapely>`_,
to perform geoprocessing efficiently while reducing implementation complexity.
Instead of requiring multiple lines of code to handle intermediate steps,
the :class:`GeoAnalyze.Raster` and :class:`GeoAnalyze.Shape` classes streamline the process by automating these operations.
This allows users to execute geoprocessing tasks more efficiently, reducing code length while ensuring accuracy and scalability.


*Raster*
^^^^^^^^^^^

- Rasterizing input geometries
- Rescaling raster resolution
- Clipping rasters using shapefiles
- Overlaying geometries onto rasters
- Reprojecting the Coordinate Reference System (CRS) 
- Handling NoData values in rasters  
- Extracting raster boundary polygons
- Reclassifying rasters values
- Counting unique raster values
- Merging raster files

*Shapefile*
^^^^^^^^^^^^^^^

- Vectorizing raster array
- Aggregating geometries
- Executing spatial joins on geometries
- Reprojecting CRS
- Filling polygons
- Performing column analysis


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