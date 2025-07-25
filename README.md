# GeoAnalyze

| <big>Status</big> | <big>Description</big> |
| --- | --- |
| **PyPI**| ![PyPI - Version](https://img.shields.io/pypi/v/GeoAnalyze) ![PyPI - Status](https://img.shields.io/pypi/status/GeoAnalyze) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/GeoAnalyze) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/GeoAnalyze) |
| **GitHub** | ![GitHub commit activity](https://img.shields.io/github/commit-activity/t/debpal/GeoAnalyze) ![GitHub last commit](https://img.shields.io/github/last-commit/debpal/GeoAnalyze) [![flake8](https://github.com/debpal/GeoAnalyze/actions/workflows/linting.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/linting.yml) [![mypy](https://github.com/debpal/GeoAnalyze/actions/workflows/typing.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/typing.yml) [![pytest](https://github.com/debpal/GeoAnalyze/actions/workflows/testing.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/testing.yml) |
| **Codecov** | [![codecov](https://codecov.io/gh/debpal/GeoAnalyze/graph/badge.svg?token=9OW3TRHI7C)](https://codecov.io/gh/debpal/GeoAnalyze)  |
| **Read** _the_ **Docs** | ![Read the Docs](https://img.shields.io/readthedocs/GeoAnalyze) |
| **PePy** | ![Pepy Total Downloads](https://img.shields.io/pepy/dt/GeoAnalyze) |
| **License** | ![GitHub License](https://img.shields.io/github/license/debpal/GeoAnalyze) |


`GeoAnalyze` is a Python package designed to streamline geoprocessing by handling internal complexities and intermediate steps. Conceptualized and launched on October 10, 2024, this package is tailored for users with limited geospatial processing experience, allowing them to focus on desired outputs. Leveraging open-source geospatial Python modules, `GeoAnalyze` aims to empower users by providing high-level geoprocessing tools with fewer lines of code. This fast package is also useful for the users who has no access of paid GIS software packages.


## Wateshed Delineation

The `GeoAnalyze.Watershed` and `GeoAnalyze.Stream` classes provide fast and scalable watershed delineation functions by leveraging the computational efficiency of the PyPI package 
[pyflwdir](https://github.com/Deltares/pyflwdir), without requiring a detailed understanding of it. These functions can be executed either individually or simultaneously.

### *Hydrology*

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

![All delineation files from DEM](https://github.com/debpal/GeoAnalyze/raw/main/docs/_static/dem_all_delineation.png)



### *Stream Network*

- Determines the adjacent downstream segment for each stream segment
- Retrieves adjacent upstream segments associated with each stream segment
- Builds full connectivity structures from upstream to downstream
- Computes connectivity structures from downstream to upstream
- Removes all upstream connectivity up to headwaters for targeted stream segments
- Merges split stream segments either between two junction points or from a junction point upstream until a headwater is reached
- Detects junctions, drainage points, main outlets, and headwaters within the stream network
- Computes Strahler and Shreve orders of stream segments
- Includes multiple functions for generating random boxes around selected stream segments


## Geoprocessing

The `GeoAnalyze` package leverages the existing PyPI packages, such as, [rasterio](https://github.com/rasterio/rasterio),
[geopandas](https://github.com/geopandas/geopandas), and [shapely](https://github.com/shapely/shapely),
to perform geoprocessing efficiently while reducing implementation complexity.
Instead of requiring multiple lines of code to handle intermediate steps,
the `GeoAnalyze.Raster` and `GeoAnalyze.Shape` classes streamline the process by automating these operations. 
Furthermore, the `GeoAnalyze.Visual` class assists in raster and vector data plotting and visualization.
This allows users to execute geoprocessing tasks more efficiently, reducing code length while ensuring accuracy and scalability.


### *Raster*
  
- Rasterizing input geometries
- Rescaling raster resolution
- Transforming raster values
- Clipping a raster using a shapefile
- Overlaying geometries onto a raster
- Managing Coordinate Reference System (CRS)
- Handling NoData values in a raster  
- Generating boundary polygons from a raster
- Reclassifying raster values
- Trimming and extending rasters
- Filling missing values in raster regions
- Computing raster statistics
- Counting unique raster values
- Extracting raster values using a mask or range filter
- Merging multiple raster files
- Rewriting a raster with a different driver


### *Shapefile*

- Vectorizing a raster array
- Aggregating geometries from multiple shapefiles
- Executing spatial joins on geometries
- Reprojecting the CRS
- Filling polygons
- Performing column operations on a shapefile


### *Visualization*

- Quick view of a raster array
- Quick view of shapefile geometries



## File Operations (Irrespective of Extensions)

When managing GIS files, each main file is often associated with several auxiliary files. For example, a shapefile
is commonly accompanied by `.shp`, `.cpg`, `.dbf`, `.prj`, and `.shx` files, which are necessary for the shapefile to function correctly.
In geoprocessing, these associated files must be handled together to prevent errors or data loss.
The `GeoAnalyze.File` class simplifies this process by ensuring that any operation performed
on a main file automatically includes its auxiliary files, making file management more efficient and error-free.

* Deleting files in a folder.
* Transferring files from the source folder to the destination folder.
* Renaming files in a folder.
* Copying files from the source folder and renames them in the destination folder.
* Extracting files with the same extension from a folder.

## Easy Installation

To install, use pip:

```bash
pip install GeoAnalyze
```

## Quickstart
A brief example of how to start:

```python
>>> import GeoAnalyze
>>> watershed = GeoAnalyze.Watershed()
>>> stream = GeoAnalyze.Stream()
```

## Documentation

For detailed information, see the [documentation](https://geoanalyze.readthedocs.io/en/latest/).

## Support

If this project has been helpful and you'd like to contribute to its development, consider sponsoring with a coffee! Support will help maintain, improve, and expand this open-source project, ensuring continued valuable tools for the community.


[![Buy Me a Coffee](https://img.shields.io/badge/☕_Buy_me_a_coffee-FFDD00?style=for-the-badge)](https://www.buymeacoffee.com/debasish_pal)






