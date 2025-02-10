================
Geoprocessing
================

This section provides an overview of the features for processing rasters and shapefiles.


Class Instance
-----------------------

To begin, instantiate the required classes as follows:


.. code-block:: python

    import GeoAnalyze
    packagedata = GeoAnalyze.PackageData()
    raster = GeoAnalyze.Raster()
    shape = GeoAnalyze.Shape()


Raster from Shapefile 
-----------------------

To generate the stream network raster from the shapefile produced in the :ref:`Delineation Outputs <delineation_outputs>` section, use the following code:


.. code-block:: python

    # stream raster
    raster.array_from_geometries(
        shape_file=r"C:\users\username\folder\stream_lines.shp",
        value_column='flw_id',
        mask_file=r"C:\users\username\folder\dem_clipped.tif",
        nodata=-9999,
        dtype='int32',
        output_file=r"C:\users\username\folder\stream_lines.tif"
    )


Rescaling Raster Resolution 
-----------------------------

Suppose the input raster has a resolution of 15.49 m, and the targeted resolution is 20 m. The following code resizes the raster resolution:


.. code-block:: python

    # rescaling raster resolution
    raster.resolution_rescaling(
        input_file=r"C:\users\username\folder\dem_clipped.tif",
        target_resolution=20, 
        resampling_method='bilinear',
        output_file=r"C:\users\username\folder\dem_clipped_20m.tif"
    )


Polygon filling 
------------------

The following code merges overlapping polygons, explodes multipart polygons, and fills any holes within the polygons.
For this, we use the lake shapefile retrieved from the :class:`GeoAnalyze.PackageData` class.



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
    
    
Extract Geometries by Spatial Join 
------------------------------------

To extract the lakes that intersect with the stream network generated in the :ref:`Delineation Outputs <delineation_outputs>` section, use the following code:


.. code-block:: python
    
    # lake extraction
    extract_gdf = shape.extract_spatial_join_geometries(
        input_file=r"C:\users\username\folder\lake_fill.shp",
        overlay_file=r"C:\users\username\folder\stream_lines.shp",
        output_file=r"C:\users\username\folder\lake_extracted.shp"
    )