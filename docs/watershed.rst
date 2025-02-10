.. _watershed_delineation:


=======================
Watershed Delineation
=======================

This section provides a brief overview of the features available for watershed delineation using a Digital Elevation Model (DEM).


Class Instance
-----------------------

To begin, instantiate the required classes as follows:


.. code-block:: python

    import GeoAnalyze
    packagedata = GeoAnalyze.PackageData()
    raster = GeoAnalyze.Raster()
    watershed = GeoAnalyze.Watershed()
    stream = GeoAnalyze.Stream()


.. _basin_area_extraction:

Basin Area Extraction
-----------------------

When open-source DEMs are downloaded for a study area, they are typically provided as rectangular raster datasets with a geographic Coordinate Reference System (CRS).
To extract the basin area from the extended DEM, a main outlet point must be specified. However, the :class:`GeoAnalyze.Watershed` class can automatically delineate the basin
by identifying the highest flow accumulation point as the main outlet. Before proceeding, the DEM must be converted to a projected CRS to ensure accurate hydrological computations.

The following code retrieves the extended DEM using the :class:`GeoAnalyze.PackageData` class, converts it to a projected CRS,
and extracts the corresponding basin area along with a clipped DEM.


.. code-block:: python

    # accessing the extended DEM of Oulanka watershed in Finland
    packagedata.raster_dem(
        dem_file=r"C:\users\username\folder\dem_extended.tif"
    )
    
    # converting geographic CRS to projected CRS 'EPSG:3067'
    raster.crs_reprojection(
        input_file=r"C:\users\username\folder\dem_extended.tif",
        resampling_method='bilinear',
        target_crs='EPSG:3067',
        output_file=r"C:\users\username\folder\dem_extended_EPSG3067.tif",
        nodata=-9999
    )
    
    # extracting basin area and clipped DEM from extended DEM
    watershed.dem_extended_area_to_basin(
        input_file=r"C:\users\username\folder\dem_extended_EPSG3067.tif",
        basin_file=r"C:\users\username\folder\basin.shp",
        output_file=r"C:\users\username\folder\dem_clipped.tif"
    )

The following figure illustrates the basin extracted from the extended DEM based on the output datasets.

.. image:: _static/dem_extended_to_basin.png
   :align: center
   
.. raw:: html

   <br><br>


.. _delineation_outputs:

Delineation Outputs
---------------------
After obtaining the basin area of the DEM, the following code computes delineation raster files for flow direction, flow accumulation, and slope. Additionally, it generates shapefiles for the stream network, main outlets, subbasins, and drainage points of the subbasins.

For the input variable `outlet_type`, the recommended main outlet type is single, as the multiple option can create more than one main outlet. Since the multiple option was used to derive the basin area from the extended DEM, it would be inconsistent to generate multiple main outlets within the basin area.

For the input variable `tacc_type`, the threshold flow accumulation type percentage considers a percentage value of the maximum flow accumulation, whereas absolute specifies the number of cells. Suppose `tacc_type` is set to 100 for the absolute threshold flow accumulation type, with a pixel resolution of 10 m. The threshold flow accumulation area is calculated as :math:`100 \times 10 \times 10 = 10000 \text{ m}^2`.


.. code-block:: python

    # DEM delineation
    watershed.dem_delineation(
        dem_file=r"C:\users\username\folder\dem_clipped.tif",
        outlet_type='single',
        tacc_type='percentage',
        tacc_value=1,
        folder_path=r"C:\users\username\folder"
    )

The following figure illustrates the flow direction, flow accumulation, stream network, and subbasins delived from the output datasets.


.. image:: _static/dem_delineation.png
   :align: center

.. raw:: html

   <br><br>


Stream Connectivity
---------------------
Stream connectivity identifies the connected downstream segment identifiers for each segment in the stream network.
The stream shapefile obtained from delineation includes a column named 'flw_id', which contains a unique identifier for each stream segment.
The following code returns the stream GeoDataFrame with an additional column, 'ds_id', representing the connected downstream segment identifiers.


.. code-block:: python

    # stream connectivity
    output = stream.connectivity_to_downstream_segment(
        input_file=r"C:\users\username\folder\stream_lines.shp",
        stream_col='flw_id',
        output_file=r"C:\users\username\folder\stream_connectivity.shp"
    )
    