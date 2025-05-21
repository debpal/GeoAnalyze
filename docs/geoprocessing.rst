================
Geoprocessing
================

This section provides an overview of the features for processing rasters and shapefiles.


Class Instance
-----------------------

To begin, instantiate the required classes as follows:


.. code-block:: python

    import GeoAnalyze
    raster = GeoAnalyze.Raster()
    shape = GeoAnalyze.Shape()
    visual = GeoAnalyze.Visual()


Raster Array from a Shapefile 
--------------------------------

To generate the stream network raster from the shapefile produced in the :ref:`Delineation Outputs <delineation_outputs>` section, use the following code:


.. code-block:: python

    # stream raster
    raster.array_from_geometries(
        shape_file=r"C:\users\username\folder\stream_lines.shp",
        value_column='flw_id',
        mask_file=r"C:\users\username\folder\dem_clipped.tif",
        output_file=r"C:\users\username\folder\stream_lines.tif"
    )


Rescaling Raster Resolution 
-----------------------------

To rescale the raster resolution (e.g., from 15.49 m to 20 m), use the following code:


.. code-block:: python

    # rescaling raster resolution
    raster.resolution_rescaling(
        input_file=r"C:\users\username\folder\dem_clipped.tif",
        target_resolution=20, 
        resampling_method='bilinear',
        output_file=r"C:\users\username\folder\dem_clipped_20m.tif"
    )
    
    
Clipping a Raster Using a Shapefile 
---------------------------------------

To clip a raster using the extent of a shapefile, use the following code:


.. code-block:: python

    # raster clipping using a shapefile
    raster.clipping_by_shapes(
        input_file=r"C:\users\username\folder\dem.tif",
        shapefile=r"C:\users\username\folder\area.shp", 
        output_file=r"C:\users\username\folder\dem_clipped.tif"
    )


Overlaying Geometries onto a Raster 
---------------------------------------

To overlay geometries from a shapefile onto a raster, use the following code:


.. code-block:: python

    # overlaying geometries to a raster
    raster.overlaid_with_geometries(
        input_file=r"C:\users\username\folder\landuse.tif",
        shapefile=r"C:\users\username\folder\stream.shp",
        value_column='flw_id',
        output_file=r"C:\users\username\folder\landuse_stream.tif"
    )

    
Reprojecting Coordinate Reference System (CRS)
------------------------------------------------

To reproject rasters and shapefiles to a different Coordinate Reference System (CRS), use the following code:


.. code-block:: python

    # reprojecting raster CRS
    raster.crs_reprojection(
        input_file=r"C:\users\username\folder\dem.tif",
        resampling_method='bilinear',
        target_crs='EPSG:3067',
        output_file=r"C:\users\username\folder\dem_crs.tif"
    )
    
    # reprojecting shapefile CRS
    shape.crs_reprojection(
        input_file=r"C:\users\username\folder\dem_boundary.shp",
        target_crs='EPSG:3067',
        output_file=r"C:\users\username\folder\dem_boundary_crs.shp"
    )
    

Trimming a Raster
--------------------

To trim rows and columns that contain only NoData values, use the following code:


.. code-block:: python

    # trimming NoData rows and columns
    raster.nodata_extent_trimming(
        input_file=r"C:\users\username\folder\dem.tif",
        output_file=r"C:\users\username\folder\dem_nodata_trim.tif"
    )
    
    
Extending a Raster
--------------------

To extend a raster to match the spatial extent of a mask raster, use the following code:


.. code-block:: python

    # extending raster to the extend of the mask raster
    raster.extension_to_mask_with_fill_value(
        input_file=r"C:\users\username\folder\input.tif",
        mask_file=r"C:\users\username\folder\mask.tif",
        fill_value=1,
        output_file=r"C:\users\username\folder\input_extended.tif"
    )

Generating Boundaries of a Raster
-----------------------------------

To generate the boundary polygons of a raster, use the following code:


.. code-block:: python

    # extracting raster boundaries
    raster.boundary_polygon(
        raster_file=r"C:\users\username\folder\dem.tif",
        shape_file=r"C:\users\username\folder\dem_boundary.shp"
    )
    
    
Computing Raster Statistics
--------------------------------

To compute basic statistics from a raster file, use the following code:


.. code-block:: python

    # raster statistics
    raster.statistics_summary(
        raster_file=r"C:\users\username\folder\landuse.tif"
    )
    
    
Computing Raster Statistics by Reference Zone
-------------------------------------------------

To compute summary statistics based on reference zones, use the following code:


.. code-block:: python

    # raster statistics by reference zone
    output = raster.statistics_summary_by_reference_zone(
        value_file=r"C:\users\username\folder\dem.tif",
        zone_file=r"C:\users\username\folder\landuse.tif",
        csv_file=r"C:\users\username\folder\statistics_dem_by_landuse.csv"
    )


Counting Raster Values
--------------------------------

To count different types of values in a raster, use the following code:


.. code-block:: python

    # counting unique values
    raster.count_unique_values(
        raster_file=r"C:\users\username\folder\landuse.tif",
        csv_file=r"C:\users\username\folder\landuse_count.csv"
    )
    
    # counting valid data cells
    raster.count_data_cells(
        raster_file=r"C:\users\username\folder\landuse.tif"
    )
    
    # counting Nodata cells
    raster.count_nodata_cells(
        raster_file=r"C:\users\username\folder\landuse.tif"
    )
    
    
Extracting Raster Values by Mask
----------------------------------------

To extract values from an input raster based on a mask raster, use the following code:


.. code-block:: python

    # extracting raster values by mask
    raster.extract_value_by_mask(
        input_file=r"C:\users\username\folder\flwdir.tif",
        mask_file=r"C:\users\username\folder\stream.tif",
        output_file=r"C:\users\username\folder\flwdir_extract.tif"
    )
    
    
Merging Raster Files
-----------------------

To merge raster files of the same type, store them in a folder (without mixing other rasters), and use the following code:


.. code-block:: python

    # merging raster files
    raster.merging_files(
        folder_path=r"C:\users\username\raster_folder",
        raster_file=r"C:\users\username\folder\merge.tif"
    )
    
    
Changing Raster Driver
----------------------------

To rewrite a raster file using a different driver, use the following code:

.. code-block:: python

    # changing raster driver
    raster.driver_convert(
        input_file=r"C:\users\username\folder\input.tif",
        target_driver='RST',
        output_file=r"C:\users\username\folder\output.rst"
    )
    
    
Vectorizing Raster Array 
--------------------------

To generate the geometries for selected values in a raster, use the following code:


.. code-block:: python

    # raster to geometries
    raster.array_to_geometries(
        raster_file=r"C:\users\username\folder\subbasin.tif",
        select_value=[5, 6],
        shapefile_file=r"C:\users\username\folder\subbasin.shp"
    )

Aggregating Geometries 
--------------------------

To aggregate geometries of a specified type from shapefiles in a folder, use the following code:


.. code-block:: python
    
    # aggregating polygon geometries
    aggregate_gdf = shape.aggregate_geometries(
        folder_path=r"C:\users\username\shapefile_folder",
        geometry_type='Polygon',
        column_name='pid',
        output_file=r"C:\users\username\folder\aggregate_polygons.shp"
    )


Extract Geometries by Spatial Join 
------------------------------------

To extract lakes that intersect with the stream network generated in the :ref:`Delineation Outputs <delineation_outputs>` section, use the following code:


.. code-block:: python
    
    # lake extraction
    extract_gdf = shape.extract_spatial_join_geometries(
        input_file=r"C:\users\username\folder\lake_fill.shp",
        overlay_file=r"C:\users\username\folder\stream_lines.shp",
        output_file=r"C:\users\username\folder\lake_extracted.shp"
    )


Filling Polygons 
------------------

The following code merges overlapping polygons, explodes multipart geometries, and fills any holes within polygons.
In this example, we use the lake shapefile obtained from the :class:`GeoAnalyze.PackageData` class. 
Before filling, we perform column operations to assign and retain an ID for each lake polygon.


.. code-block:: python

    # accessing lake shapefile
    lake_gdf = packagedata.geodataframe_lake
    lake_file = r"C:\users\username\folder\lake.shp"
    lake_gdf.to_file(lake_file)  
    
    # adding ID column
    lake_gdf = shape.column_add_for_id(
        input_file=lake_file,
        column_name='lid',
        output_file=lake_file
    )
    
    # retaining ID column only
    lake_gdf = shape.column_retain(
        input_file=lake_file,
        retain_cols=['lid'],
        output_file=lake_file
    )
    
    # fill polygons after merging, if any
    lake_gdf = shape.polygon_fill_after_merge(
        input_file=lake_file,
        column_name='lid',
        output_file=r"C:\users\username\folder\lake_fill.shp"
    )
    
    
Quick Visualization of Geospatial Data 
-----------------------------------------

To get a quick view of the input geospatial data without customization, use the following code:


.. code-block:: python
    
    # raster quick view
    visual.quickview_raster(
        raster_file=r"C:\users\username\folder\input_raster.tif",
        figure_file=r"C:\users\username\folder\output_figure.png",
        gui_window=False
    )

    # raster quick view with color map in log scale
    visual.quickview_raster(
        raster_file=r"C:\users\username\folder\input_raster.tif",
        figure_file=r"C:\users\username\folder\output_figure.png",
        log_scale=True,
        gui_window=False
    )
    
    # shapefile column quick view
    visual.quickview_geometry(
        shape_file=r"C:\users\username\folder\input_shape.tif",
        column_name='target_column'
        figure_file=r"C:\users\username\folder\output_figure.png"
    )
